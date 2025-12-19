from rest_framework import serializers
from .models import Rooms, Bookings
from django.db.models import Q

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rooms
        fields = '__all__'

    def validate(self, data):
        # Validation: Check if room_name exists in this Organization
        room_name = data.get('room_name')
        organization = data.get('organizationid')
        
        # If this is an update, we exclude the current instance to avoid false positives
        instance = self.instance 
        
        query = Rooms.objects.filter(
            room_name__iexact=room_name, 
            organizationid=organization
        )
        
        if instance:
            query = query.exclude(pk=instance.pk)

        if query.exists():
            raise serializers.ValidationError(
                {"room_name": "A room with this name already exists in your organization."}
            )
            
        return data


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookings
        fields = '__all__'

    def validate(self, data):
        room = data.get('room')
        booking_date = data.get('booking_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        # 1. Basic check: Start time must be before end time
        if start_time >= end_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})

        # 2. Overlap Validation
        # Overlap Logic: (StartA < EndB) and (EndA > StartB)
        overlapping_bookings = Bookings.objects.filter(
            room=room,
            booking_date=booking_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        # If this is an update (PUT/PATCH), exclude the current booking
        if self.instance:
            overlapping_bookings = overlapping_bookings.exclude(pk=self.instance.pk)

        if overlapping_bookings.exists():
            raise serializers.ValidationError(
                "This room is already booked for the selected time slot."
            )

        return data