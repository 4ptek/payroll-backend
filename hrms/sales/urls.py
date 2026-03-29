from django.urls import path
from .views import (
    SalesTeamCreateView,
    SalesTeamListView,
    SalesTeamDetailView,
    SalesTeamMemberAddView,
    SalesTeamMemberRemoveView,
    CommissionStructureCreateView,
    CommissionStructureListView,
    SalesTargetCreateView,
    SalesTargetListView,
    SalesEntryCreateView,
    SalesEntryListView,
    SalesEntryVerifyView,
    SalesReportGenerateView,
    SalesReportMonthlyView,
)

urlpatterns = [
    path('teams/', SalesTeamCreateView.as_view(), name='sales-team-create'),
    path('teams/list', SalesTeamListView.as_view(), name='sales-team-list'),
    path('teams/<int:team_id>/', SalesTeamDetailView.as_view(), name='sales-team-detail'),
    path('teams/<int:team_id>/members/add', SalesTeamMemberAddView.as_view(), name='sales-team-member-add'),
    path('teams/<int:team_id>/members/remove', SalesTeamMemberRemoveView.as_view(), name='sales-team-member-remove'),
    path('commission/', CommissionStructureCreateView.as_view(), name='sales-commission-create'),
    path('commission/list', CommissionStructureListView.as_view(), name='sales-commission-list'),
    path('targets/', SalesTargetCreateView.as_view(), name='sales-target-create'),
    path('targets/list', SalesTargetListView.as_view(), name='sales-target-list'),
    path('entry/', SalesEntryCreateView.as_view(), name='sales-entry-create'),
    path('entry/list', SalesEntryListView.as_view(), name='sales-entry-list'),
    path('entry/<int:entry_id>/verify', SalesEntryVerifyView.as_view(), name='sales-entry-verify'),
    path('report/generate', SalesReportGenerateView.as_view(), name='sales-report-generate'),
    path('report/monthly', SalesReportMonthlyView.as_view(), name='sales-report-monthly'),

]