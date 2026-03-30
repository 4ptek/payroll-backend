from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.db import connection
from django.db.models import Sum, Q
from decimal import Decimal

from .models import (
    SalesTeams,
    SalesTeamMembers,
    SalesCommissionStructures,
    SalesTargets,
    SalesEntries,
    SalesMonthlyReports,
)
from .serializers import (
    SalesTeamCreateSerializer,
    SalesTeamListSerializer,
    SalesTeamDetailSerializer,
    SalesTeamMemberAddSerializer,
    SalesTeamMemberRemoveSerializer,
    CommissionStructureCreateSerializer,
    CommissionStructureListSerializer,
    SalesTargetCreateSerializer,
    SalesTargetListSerializer,
    SalesEntryCreateSerializer,
    SalesEntryListSerializer,
    SalesEntryVerifySerializer,
    SalesReportGenerateSerializer,
    SalesMonthlyReportSerializer,
    calculate_commission,
)

def get_org(request):
    return getattr(request.user, 'organizationid', None)

def get_next_id(sequence_name):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT nextval('{sequence_name}')")
        return cursor.fetchone()[0]

# 1. SALES TEAMS
class SalesTeamCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SalesTeamCreateSerializer(data=request.data)

        if serializer.is_valid():
            try:
                org = get_org(request)
                if not org:
                    return Response({
                        "message": "User is not associated with any Organization.",
                        "status": status.HTTP_403_FORBIDDEN
                    }, status=status.HTTP_403_FORBIDDEN)

                serializer.save(
                    id=get_next_id('sales_teams_id_seq'),
                    organizationid=org,
                    createdby=request.user,
                    createdat=timezone.now(),
                    isactive=True,
                    isdelete=False,
                )

                return Response({
                    "data": serializer.data,
                    "message": "Sales team created successfully.",
                    "status": status.HTTP_201_CREATED
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    "message": f"Error: {str(e)}",
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "data": serializer.errors,
            "message": "Validation Error",
            "status": status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)


class SalesTeamListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            teams = SalesTeams.objects.filter(
                organizationid=org,
                isactive=True,
                isdelete=False
            )

            # Optional filter by department
            dept_id = request.query_params.get('department')
            if dept_id:
                teams = teams.filter(departmentid=dept_id)

            serializer = SalesTeamListSerializer(teams, many=True)

            return Response({
                "data": serializer.data,
                "message": "Sales teams fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesTeamDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_team(self, team_id, org):
        try:
            return SalesTeams.objects.get(id=team_id, organizationid=org, isdelete=False)
        except SalesTeams.DoesNotExist:
            return None

    def get(self, request, team_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            team = self.get_team(team_id, org)
            if not team:
                return Response({
                    "message": "Team not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = SalesTeamDetailSerializer(team)

            return Response({
                "data": serializer.data,
                "message": "Team details fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, team_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            team = self.get_team(team_id, org)
            if not team:
                return Response({
                    "message": "Team not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = SalesTeamCreateSerializer(team, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(
                    updatedby=request.user,
                    updateat=timezone.now()
                )
                return Response({
                    "data": serializer.data,
                    "message": "Team updated successfully.",
                    "status": status.HTTP_200_OK
                }, status=status.HTTP_200_OK)

            return Response({
                "data": serializer.errors,
                "message": "Validation Error",
                "status": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, team_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            team = self.get_team(team_id, org)
            if not team:
                return Response({
                    "message": "Team not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            # Soft delete
            team.isdelete = True
            team.isactive = False
            team.deletedby = request.user
            team.deleteat = timezone.now()
            team.save()

            return Response({
                "message": "Team deleted successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 2. SALES TEAM MEMBERS
class SalesTeamMemberAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, team_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            try:
                team = SalesTeams.objects.get(id=team_id, organizationid=org, isdelete=False)
            except SalesTeams.DoesNotExist:
                return Response({
                    "message": "Team not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = SalesTeamMemberAddSerializer(
                data=request.data,
                context={'team': team}
            )

            if serializer.is_valid():
                serializer.save(
                    id=get_next_id('sales_team_members_id_seq'),
                    teamid=team,
                    organizationid=org,
                    createdby=request.user,
                    createdat=timezone.now(),
                    isactive=True,
                    isdelete=False,
                )
                return Response({
                    "data": serializer.data,
                    "message": "Member added to team successfully.",
                    "status": status.HTTP_201_CREATED
                }, status=status.HTTP_201_CREATED)

            return Response({
                "data": serializer.errors,
                "message": "Validation Error",
                "status": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesTeamMemberRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, team_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = SalesTeamMemberRemoveSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "data": serializer.errors,
                    "message": "Validation Error",
                    "status": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)

            employee_id = serializer.validated_data['employeeid']

            try:
                member = SalesTeamMembers.objects.get(
                    teamid=team_id,
                    employeeid=employee_id,
                    isactive=True,
                    isdelete=False
                )
            except SalesTeamMembers.DoesNotExist:
                return Response({
                    "message": "Ye employee is team ka active member nahi hai.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            # Soft remove — leavingdate set karo
            member.isactive = False
            member.leavingdate = timezone.now().date()
            member.updatedby = request.user
            member.updateat = timezone.now()
            member.save()

            return Response({
                "message": "Member removed from team successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 3. COMMISSION STRUCTURES
class CommissionStructureCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CommissionStructureCreateSerializer(data=request.data)

        if serializer.is_valid():
            try:
                org = get_org(request)
                if not org:
                    return Response({
                        "message": "User is not associated with any Organization.",
                        "status": status.HTTP_403_FORBIDDEN
                    }, status=status.HTTP_403_FORBIDDEN)

                serializer.save(
                    id=get_next_id('sales_commission_structures_id_seq'),
                    organizationid=org,
                    createdby=request.user,
                    createdat=timezone.now(),
                    isactive=True,
                    isdelete=False,
                )

                return Response({
                    "data": serializer.data,
                    "message": "Commission structure created successfully.",
                    "status": status.HTTP_201_CREATED
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    "message": f"Error: {str(e)}",
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "data": serializer.errors,
            "message": "Validation Error",
            "status": status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)


class CommissionStructureListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            structures = SalesCommissionStructures.objects.filter(
                organizationid=org,
                isactive=True,
                isdelete=False
            )

            # Optional filters
            applylevel = request.query_params.get('applylevel')
            team_id    = request.query_params.get('team')
            emp_id     = request.query_params.get('employee')

            if applylevel:
                structures = structures.filter(applylevel=applylevel.upper())
            if team_id:
                structures = structures.filter(teamid=team_id)
            if emp_id:
                structures = structures.filter(employeeid=emp_id)

            serializer = CommissionStructureListSerializer(structures, many=True)

            return Response({
                "data": serializer.data,
                "message": "Commission structures fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 4. SALES TARGETS
class SalesTargetCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SalesTargetCreateSerializer(data=request.data)

        if serializer.is_valid():
            try:
                org = get_org(request)
                if not org:
                    return Response({
                        "message": "User is not associated with any Organization.",
                        "status": status.HTTP_403_FORBIDDEN
                    }, status=status.HTTP_403_FORBIDDEN)

                serializer.save(
                    id=get_next_id('sales_targets_id_seq'),
                    organizationid=org,
                    createdby=request.user,
                    createdat=timezone.now(),
                    isactive=True,
                    isdelete=False,
                )

                return Response({
                    "data": serializer.data,
                    "message": "Sales target set successfully.",
                    "status": status.HTTP_201_CREATED
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    "message": f"Error: {str(e)}",
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "data": serializer.errors,
            "message": "Validation Error",
            "status": status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)


class SalesTargetListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            targets = SalesTargets.objects.filter(
                organizationid=org,
                isactive=True,
                isdelete=False
            )

            # Optional filters
            month   = request.query_params.get('month')
            year    = request.query_params.get('year')
            team_id = request.query_params.get('team')
            emp_id  = request.query_params.get('employee')
            level   = request.query_params.get('level')

            if month:
                targets = targets.filter(targetmonth=month)
            if year:
                targets = targets.filter(targetyear=year)
            if team_id:
                targets = targets.filter(teamid=team_id)
            if emp_id:
                targets = targets.filter(employeeid=emp_id)
            if level:
                targets = targets.filter(targetlevel=level.upper())

            serializer = SalesTargetListSerializer(targets, many=True)

            return Response({
                "data": serializer.data,
                "message": "Sales targets fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 5. SALES ENTRIES (Daily)
class SalesEntryCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SalesEntryCreateSerializer(data=request.data)

        if serializer.is_valid():
            try:
                org = get_org(request)
                if not org:
                    return Response({
                        "message": "User is not associated with any Organization.",
                        "status": status.HTTP_403_FORBIDDEN
                    }, status=status.HTTP_403_FORBIDDEN)
                    
                employee = getattr(request.user, 'employeeid', None)
                if not employee:
                    return Response({
                        "message": "No employee record linked to this user.",
                        "status": status.HTTP_403_FORBIDDEN
                    }, status=status.HTTP_403_FORBIDDEN)

                team_membership = SalesTeamMembers.objects.filter(
                    employeeid=employee,
                    isactive=True,
                    isdelete=False
                ).first()
                team = team_membership.teamid if team_membership else None

                serializer.save(
                    id=get_next_id('sales_entries_id_seq'),
                    organizationid=org,
                    employeeid=employee,
                    teamid=team,
                    createdby=request.user,
                    createdat=timezone.now(),
                    isverified=False,
                    isactive=True,
                    isdelete=False,
                )

                return Response({
                    "data": serializer.data,
                    "message": "Sales entry added successfully.",
                    "status": status.HTTP_201_CREATED
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    "message": f"Error: {str(e)}",
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "data": serializer.errors,
            "message": "Validation Error",
            "status": status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)


class SalesEntryListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            entries = SalesEntries.objects.filter(
                organizationid=org,
                isactive=True,
                isdelete=False
            ).order_by('-saledate')

            # Optional filters
            emp_id   = request.query_params.get('employee')
            team_id  = request.query_params.get('team')
            date     = request.query_params.get('date')
            month    = request.query_params.get('month')
            year     = request.query_params.get('year')
            verified = request.query_params.get('verified')

            if emp_id:
                entries = entries.filter(employeeid=emp_id)
            if team_id:
                entries = entries.filter(teamid=team_id)
            if date:
                entries = entries.filter(saledate=date)
            if month:
                entries = entries.filter(saledate__month=month)
            if year:
                entries = entries.filter(saledate__year=year)
            if verified is not None:
                is_verified = verified.lower() == 'true'
                entries = entries.filter(isverified=is_verified)

            serializer = SalesEntryListSerializer(entries, many=True)

            return Response({
                "data": serializer.data,
                "message": "Sales entries fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesEntryVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, entry_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            try:
                entry = SalesEntries.objects.get(
                    id=entry_id,
                    organizationid=org,
                    isdelete=False
                )
            except SalesEntries.DoesNotExist:
                return Response({
                    "message": "Sales entry not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = SalesEntryVerifySerializer(entry, data=request.data, partial=True)
            if serializer.is_valid():
                # Verifier info set karo
                entry.isverified = serializer.validated_data.get('isverified')
                entry.verifiedby = getattr(request.user, 'employeeid', None)
                entry.verifiedat = timezone.now()
                entry.updatedby = request.user
                entry.updateat = timezone.now()
                entry.save()

                return Response({
                    "message": "Entry verification updated successfully.",
                    "status": status.HTTP_200_OK
                }, status=status.HTTP_200_OK)

            return Response({
                "data": serializer.errors,
                "message": "Validation Error",
                "status": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 6. SALES MONTHLY REPORT
def _get_active_commission(employee, team, month, year):
    from datetime import date
    report_date = date(year, month, 1)
    
    # 1. Individual level commission (priority)
    individual_commission = SalesCommissionStructures.objects.filter(
        employeeid=employee,
        applylevel='INDIVIDUAL',
        isactive=True,
        isdelete=False,
        effectivefrom__lte=report_date
    ).filter(
        Q(effectiveto__isnull=True) | Q(effectiveto__gte=report_date)
    ).first()

    if individual_commission:
        return individual_commission

    # 2. Team level commission (fallback)
    if team:
        team_commission = SalesCommissionStructures.objects.filter(
            teamid=team,
            applylevel='TEAM',
            isactive=True,
            isdelete=False,
            effectivefrom__lte=report_date
        ).filter(
            Q(effectiveto__isnull=True) | Q(effectiveto__gte=report_date)
        ).first()

        if team_commission:
            return team_commission

    return None


# def _generate_report_for_employee(employee, org, month, year, requested_by):
#     # 1. Is employee ka team nikalo
#     membership = SalesTeamMembers.objects.filter(
#         employeeid=employee,
#         isactive=True,
#         isdelete=False
#     ).first()
#     team = membership.teamid if membership else None

#     # 2. Individual sales total (sirf verified entries)
#     individual_sales_agg = SalesEntries.objects.filter(
#         employeeid=employee,
#         organizationid=org,
#         saledate__month=month,
#         saledate__year=year,
#         isverified=True,
#         isdelete=False
#     ).aggregate(total=Sum('totalamount'))
#     total_individual_sales = individual_sales_agg['total'] or Decimal('0.00')

#     # 3. Team sales total
#     total_team_sales = Decimal('0.00')
#     if team:
#         team_sales_agg = SalesEntries.objects.filter(
#             teamid=team,
#             organizationid=org,
#             saledate__month=month,
#             saledate__year=year,
#             isverified=True,
#             isdelete=False
#         ).aggregate(total=Sum('totalamount'))
#         total_team_sales = team_sales_agg['total'] or Decimal('0.00')

#     # 4. Individual target
#     individual_target_obj = SalesTargets.objects.filter(
#         employeeid=employee,
#         targetlevel='INDIVIDUAL',
#         targetmonth=month,
#         targetyear=year,
#         isdelete=False
#     ).first()
#     individual_target = individual_target_obj.targetamount if individual_target_obj else None

#     # 5. Team target
#     team_target = None
#     if team:
#         team_target_obj = SalesTargets.objects.filter(
#             teamid=team,
#             targetlevel='TEAM',
#             targetmonth=month,
#             targetyear=year,
#             isdelete=False
#         ).first()
#         team_target = team_target_obj.targetamount if team_target_obj else None

#     # 6. Achievement percentage — individual pe based
#     achievement_pct = None
#     if individual_target and individual_target > 0:
#         achievement_pct = round((total_individual_sales / individual_target) * 100, 2)

#     # 7. Commission structure — individual override > team fallback
#     commission_structure = _get_active_commission(employee, team, month, year)

#     # 8. Commission calculate karo
#     commission_earned = calculate_commission(commission_structure, total_individual_sales)

#     # 9. Basic salary snapshot (employees table se)
#     basic_salary = employee.basicsalary or Decimal('0.00')

#     # 10. Total payout
#     total_payout = basic_salary + commission_earned

#     # 11. Report save ya update karo
#     report, created = SalesMonthlyReports.objects.update_or_create(
#         employeeid=employee,
#         reportmonth=month,
#         reportyear=year,
#         defaults={
#             'organizationid': org,
#             'teamid': team,
#             'individualtarget': individual_target,
#             'teamtarget': team_target,
#             'totalindividualsales': total_individual_sales,
#             'totalteamsales': total_team_sales,
#             'achievementpercentage': achievement_pct,
#             'basicsalary': basic_salary,
#             'commissionearned': commission_earned,
#             'totalpayout': total_payout,
#             'commissionstructureid': commission_structure,
#             'isgeneratedmanually': True,
#             'generatedat': timezone.now(),
#             'generatedby': requested_by,
#             'isactive': True,
#             'isdelete': False,
#             'createdat': timezone.now(),
#             'createdby': requested_by,
#             'updateat': timezone.now(),
#             'updatedby': requested_by,
#         }
#     )

#     return report, created, None

def _generate_report_for_employee(employee, org, month, year, requested_by):
    from decimal import Decimal

    # 1. Team nikaalo
    membership = SalesTeamMembers.objects.filter(
        employeeid=employee,
        isactive=True,
        isdelete=False
    ).first()
    team = membership.teamid if membership else None

    # 2. Individual sales
    individual_sales_agg = SalesEntries.objects.filter(
        employeeid=employee,
        organizationid=org,
        saledate__month=month,
        saledate__year=year,
        isverified=True,
        isdelete=False
    ).aggregate(total=Sum('totalamount'))

    total_individual_sales = individual_sales_agg['total'] or Decimal('0.00')

    # 3. Team sales
    total_team_sales = Decimal('0.00')
    if team:
        team_sales_agg = SalesEntries.objects.filter(
            teamid=team,
            organizationid=org,
            saledate__month=month,
            saledate__year=year,
            isverified=True,
            isdelete=False
        ).aggregate(total=Sum('totalamount'))

        total_team_sales = team_sales_agg['total'] or Decimal('0.00')

    # 4. Individual target
    individual_target_obj = SalesTargets.objects.filter(
        employeeid=employee,
        targetlevel='INDIVIDUAL',
        targetmonth=month,
        targetyear=year,
        isdelete=False
    ).first()

    individual_target = individual_target_obj.targetamount if individual_target_obj else None

    # 5. Team target
    team_target = None
    if team:
        team_target_obj = SalesTargets.objects.filter(
            teamid=team,
            targetlevel='TEAM',
            targetmonth=month,
            targetyear=year,
            isdelete=False
        ).first()

        team_target = team_target_obj.targetamount if team_target_obj else None

    # 6. Achievement %
    achievement_pct = None
    if individual_target and individual_target > 0:
        achievement_pct = round((total_individual_sales / individual_target) * 100, 2)

    # 7. Commission structure
    commission_structure = _get_active_commission(employee, team, month, year)

    # 8. Commission calculate
    commission_earned = calculate_commission(
        commission_structure,
        total_individual_sales
    )

    # 9. Basic salary
    basic_salary = employee.basicsalary or Decimal('0.00')

    # 10. Total payout
    total_payout = basic_salary + commission_earned

    # 11. MANUAL UPDATE / CREATE LOGIC

    existing_report = SalesMonthlyReports.objects.filter(
        employeeid=employee,
        reportmonth=month,
        reportyear=year
    ).first()

    if existing_report:
        existing_report.organizationid = org
        existing_report.teamid = team
        existing_report.individualtarget = individual_target
        existing_report.teamtarget = team_target
        existing_report.totalindividualsales = total_individual_sales
        existing_report.totalteamsales = total_team_sales
        existing_report.achievementpercentage = achievement_pct
        existing_report.basicsalary = basic_salary
        existing_report.commissionearned = commission_earned
        existing_report.totalpayout = total_payout
        existing_report.commissionstructureid = commission_structure
        existing_report.isgeneratedmanually = True
        existing_report.generatedat = timezone.now()
        existing_report.generatedby = requested_by
        existing_report.isactive = True
        existing_report.isdelete = False
        existing_report.updateat = timezone.now()
        existing_report.updatedby = requested_by

        existing_report.save()

        return existing_report, False, None

    else:
        report = SalesMonthlyReports.objects.create(
            id=get_next_id('sales_monthly_reports_id_seq'),  # 👈 FIX
            employeeid=employee,
            reportmonth=month,
            reportyear=year,
            organizationid=org,
            teamid=team,
            individualtarget=individual_target,
            teamtarget=team_target,
            totalindividualsales=total_individual_sales,
            totalteamsales=total_team_sales,
            achievementpercentage=achievement_pct,
            basicsalary=basic_salary,
            commissionearned=commission_earned,
            totalpayout=total_payout,
            commissionstructureid=commission_structure,
            isgeneratedmanually=True,
            generatedat=timezone.now(),
            generatedby=requested_by,
            isactive=True,
            isdelete=False,
            createdat=timezone.now(),
            createdby=requested_by,
            updateat=timezone.now(),
            updatedby=requested_by,
        )

        return report, True, None

class SalesReportGenerateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SalesReportGenerateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "data": serializer.errors,
                "message": "Validation Error",
                "status": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            month    = serializer.validated_data['reportmonth']
            year     = serializer.validated_data['reportyear']
            team_id  = serializer.validated_data.get('teamid')
            emp_id   = serializer.validated_data.get('employeeid')

            employees_to_process = []

            if emp_id:
                # Mode 2: Single employee
                from employee.models import Employees  
                try:
                    emp = Employees.objects.get(id=emp_id, organizationid=org, isdelete=False)
                    employees_to_process = [emp]
                except Employees.DoesNotExist:
                    return Response({
                        "message": "Employee not found.",
                        "status": status.HTTP_404_NOT_FOUND
                    }, status=status.HTTP_404_NOT_FOUND)

            elif team_id:
                # Mode 1: Team ke sare active members
                try:
                    team = SalesTeams.objects.get(id=team_id, organizationid=org, isdelete=False)
                except SalesTeams.DoesNotExist:
                    return Response({
                        "message": "Team not found.",
                        "status": status.HTTP_404_NOT_FOUND
                    }, status=status.HTTP_404_NOT_FOUND)

                memberships = SalesTeamMembers.objects.filter(
                    teamid=team,
                    isactive=True,
                    isdelete=False
                ).select_related('employeeid')
                employees_to_process = [m.employeeid for m in memberships]

            else:
                # Mode 3: Puri org ke sare employees jo kisi team mein hain
                memberships = SalesTeamMembers.objects.filter(
                    organizationid=org,
                    isactive=True,
                    isdelete=False
                ).select_related('employeeid')
                employees_to_process = list({m.employeeid.id: m.employeeid for m in memberships}.values())

            if not employees_to_process:
                return Response({
                    "message": "Koi bhi employee process karne ke liye nahi mila.",
                    "status": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)

            # Sare employees process karo
            generated = []
            updated = []
            errors = []

            for employee in employees_to_process:
                report, created, err = _generate_report_for_employee(
                    employee, org, month, year, request.user
                )
                if err:
                    errors.append({"employee": employee.id, "error": err})
                elif created:
                    generated.append(employee.id)
                else:
                    updated.append(employee.id)

            return Response({
                "data": {
                    "generated_count": len(generated),
                    "updated_count": len(updated),
                    "error_count": len(errors),
                    "errors": errors,
                    "month": month,
                    "year": year,
                },
                "message": f"Report generation complete. {len(generated)} created, {len(updated)} updated.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesReportMonthlyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            reports = SalesMonthlyReports.objects.filter(
                organizationid=org,
                isactive=True,
                isdelete=False
            ).order_by('-reportyear', '-reportmonth')

            # Filters
            month   = request.query_params.get('month')
            year    = request.query_params.get('year')
            team_id = request.query_params.get('team')
            emp_id  = request.query_params.get('employee')

            if month:
                reports = reports.filter(reportmonth=month)
            if year:
                reports = reports.filter(reportyear=year)
            if team_id:
                reports = reports.filter(teamid=team_id)
            if emp_id:
                reports = reports.filter(employeeid=emp_id)

            serializer = SalesMonthlyReportSerializer(reports, many=True)

            # Summary stats — agar team filter laga hai
            summary = {}
            if team_id and month and year:
                team_reports = reports
                total_sales  = sum(r.totalindividualsales or 0 for r in team_reports)
                total_payout = sum(r.totalpayout or 0 for r in team_reports)
                top_performer = max(
                    team_reports,
                    key=lambda r: r.totalindividualsales or 0,
                    default=None
                )
                summary = {
                    "team_total_sales": round(total_sales, 2),
                    "team_total_payout": round(total_payout, 2),
                    "top_performer_employee_id": top_performer.employeeid.id if top_performer else None,
                }

            return Response({
                "data": serializer.data,
                "summary": summary,
                "message": "Monthly reports fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)