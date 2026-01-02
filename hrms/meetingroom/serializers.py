from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .models import Rooms, Bookings, Bookinginvited
from user_rbac.models import Modules
from workflow.utils import initiate_workflow
from .utils import generate_unique_otp
from organization.serializers import OrganizationSerializer

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rooms
        fields = '__all__'

    def validate(self, data):
        room_name = data.get('room_name')
        organization = data.get('organizationid')
        instance = self.instance 
        
        query = Rooms.objects.filter(
            room_name__iexact=room_name, 
            organizationid=organization
        )
        if instance:
            query = query.exclude(pk=instance.pk)

        if query.exists():
            raise serializers.ValidationError({"room_name": "A room with this name already exists in your organization."})
        return data

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if instance.organizationid:
            response['organizationid'] = {
                "id": instance.organizationid.id,
                "name": instance.organizationid.name  
                #ADD detail as per needed 
            }
        return response


class BookingSerializer(serializers.ModelSerializer):
    invited_ids = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=False
    )

    class Meta:
        model = Bookings
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'otp'] 

    def validate(self, data):
        room = data.get('room')
        booking_date = data.get('booking_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})

        overlapping_bookings = Bookings.objects.filter(
            room=room,
            booking_date=booking_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        if self.instance:
            overlapping_bookings = overlapping_bookings.exclude(pk=self.instance.pk)

        if overlapping_bookings.exists():
            raise serializers.ValidationError("This room is already booked for the selected time slot.")

        return data

    def create(self, validated_data):
        invited_ids = validated_data.pop('invited_ids', [])
        
        request = self.context.get('request')
        user = request.user

        validated_data['created_by'] = user
        validated_data['created_at'] = timezone.now()
        validated_data['otp'] = generate_unique_otp()
        validated_data['status'] = 'Pending'
        
        with transaction.atomic():
            # A. Create Booking
            booking_instance = super().create(validated_data)

            # B. Create Invited People
            if invited_ids:
                invited_objects = [
                    Bookinginvited(
                        bookingid=booking_instance,
                        userid_id=uid,
                        created_at=timezone.now(),
                        isactive=True,
                        isdelete=False
                    ) for uid in invited_ids
                ]
                Bookinginvited.objects.bulk_create(invited_objects)

            # C. Workflow Trigger Logic
            try:
                org_instance = getattr(user, 'organizationid', None)
                initiator = getattr(user, 'employeeid', None)
                module_id_val = 63
                try:
                    module_instance = Modules.objects.get(pk=module_id_val)
                except Modules.DoesNotExist:
                    print("Module not found for Booking Workflow")
                    module_instance = None

                # Initiate
                if initiator and org_instance and module_instance:
                    initiate_workflow(
                        record_id=booking_instance.booking_id, 
                        module_id=module_instance,
                        organization_id=org_instance,
                        initiator_employee=initiator,
                        user=user
                    )
                    print(f"Workflow initiated for Booking ID: {booking_instance.pk}")
                else:
                    print("Skipped Workflow: Missing Initiator, Org ID, or Module")

            except Exception as e:
                print(f"Exception in Booking Workflow Block: {str(e)}")

            return booking_instance

    def to_representation(self, instance):
        response = super().to_representation(instance)
        
        # 1. Room
        if instance.room:
            response['room'] = RoomSerializer(instance.room).data
            
        # 2. Organization
        if instance.organizationid:
            response['organizationid'] = {
                "id": instance.organizationid.id,
                "name": instance.organizationid.name
            }

        # 3. Invited People (Display Names)
        invited_people = []
        for invite in instance.bookinginvited_set.all():
            if invite.userid:
                invited_people.append({
                    "id": invite.userid.id,
                    "name": invite.userid.username
                })
        
        response['invited_people'] = invited_people

        return response