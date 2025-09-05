from django.db import migrations

def create_temp_tenant(apps, schema_editor):
    ReportingTenant = apps.get_model('demoapp', 'ReportingTenant')
    Tenant = apps.get_model('demoapp', 'Tenant')

    # default reporting tenant
    reporting, _ = ReportingTenant.objects.get_or_create(
        name="Default Reporting Tenant",
        short_code="DRT001",
        defaults={"status": True},
    )

    # temp tenant
    Tenant.objects.get_or_create(
        name="TEMP Tenant",
        short_code="TDT001",
        reporting_tenant=reporting,
        defaults={"status": True},
    )

def remove_temp_tenant(apps, schema_editor):
    Tenant = apps.get_model('demoapp', 'Tenant')
    Tenant.objects.filter(short_code="TEMP_T").delete()

class Migration(migrations.Migration):

    dependencies = [
        ("demoapp", "0002_alter_address_latitude_alter_address_longitude_and_more"),
    ]

    operations = [
        migrations.RunPython(create_temp_tenant, remove_temp_tenant),
    ]
