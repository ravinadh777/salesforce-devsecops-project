#!/bin/bash

ORG="ravinadh.biyyala-s6re@force.com"
BASE="force-app/main/default"

echo "🚀 Building Enterprise Hospital App..."

mkdir -p $BASE/objects/Patient__c
mkdir -p $BASE/objects/Doctor__c/fields
mkdir -p $BASE/objects/Appointment__c/fields
mkdir -p $BASE/objects/Prescription__c/fields
mkdir -p $BASE/classes
mkdir -p $BASE/triggers

# =========================
# PATIENT OBJECT
# =========================
cat <<EOF > $BASE/objects/Patient__c/Patient__c.object-meta.xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Patient</label>
    <pluralLabel>Patients</pluralLabel>
    <nameField>
        <type>Text</type>
        <label>Patient Name</label>
    </nameField>
    <deploymentStatus>Deployed</deploymentStatus>
    <sharingModel>ReadWrite</sharingModel>
</CustomObject>
EOF

# =========================
# DOCTOR OBJECT
# =========================
cat <<EOF > $BASE/objects/Doctor__c/Doctor__c.object-meta.xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Doctor</label>
    <pluralLabel>Doctors</pluralLabel>
    <nameField>
        <type>Text</type>
        <label>Doctor Name</label>
    </nameField>
    <deploymentStatus>Deployed</deploymentStatus>
    <sharingModel>ReadWrite</sharingModel>
</CustomObject>
EOF

cat <<EOF > $BASE/objects/Doctor__c/fields/Availability__c.field-meta.xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Availability__c</fullName>
    <label>Availability</label>
    <type>Checkbox</type>
    <defaultValue>true</defaultValue>
</CustomField>
EOF

# =========================
# APPOINTMENT OBJECT
# =========================
cat <<EOF > $BASE/objects/Appointment__c/Appointment__c.object-meta.xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Appointment</label>
    <pluralLabel>Appointments</pluralLabel>
    <nameField>
        <type>AutoNumber</type>
        <label>Appointment Number</label>
        <displayFormat>APP-{0000}</displayFormat>
    </nameField>
    <deploymentStatus>Deployed</deploymentStatus>
    <sharingModel>ReadWrite</sharingModel>
</CustomObject>
EOF

# Fields
cat <<EOF > $BASE/objects/Appointment__c/fields/Appointment_Date__c.field-meta.xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Appointment_Date__c</fullName>
    <label>Appointment Date</label>
    <type>DateTime</type>
</CustomField>
EOF

cat <<EOF > $BASE/objects/Appointment__c/fields/Patient__c.field-meta.xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Patient__c</fullName>
    <label>Patient</label>
    <type>Lookup</type>
    <referenceTo>Patient__c</referenceTo>
    <relationshipName>Appointments</relationshipName>
</CustomField>
EOF

cat <<EOF > $BASE/objects/Appointment__c/fields/Doctor__c.field-meta.xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Doctor__c</fullName>
    <label>Doctor</label>
    <type>Lookup</type>
    <referenceTo>Doctor__c</referenceTo>
    <relationshipName>DoctorAppointments</relationshipName>
</CustomField>
EOF

cat <<EOF > $BASE/objects/Appointment__c/fields/Status__c.field-meta.xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Status__c</fullName>
    <label>Status</label>
    <type>Picklist</type>
    <valueSet>
        <valueSetDefinition>
            <value><fullName>Scheduled</fullName></value>
            <value><fullName>Completed</fullName></value>
            <value><fullName>Cancelled</fullName></value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
EOF

# =========================
# APEX CLASS
# =========================
cat <<EOF > $BASE/classes/AppointmentService.cls
public with sharing class AppointmentService {

    public static Appointment__c createAppointment(Id patientId, Id doctorId, Datetime apptDate) {

        if (patientId == null || doctorId == null) {
            throw new AuraHandledException('Invalid input');
        }

        Doctor__c d = [SELECT Availability__c FROM Doctor__c WHERE Id = :doctorId LIMIT 1];

        if (!d.Availability__c) {
            throw new AuraHandledException('Doctor not available');
        }

        Appointment__c a = new Appointment__c(
            Patient__c = patientId,
            Doctor__c = doctorId,
            Appointment_Date__c = apptDate,
            Status__c = 'Scheduled'
        );

        insert a;
        return a;
    }
}
EOF

# =========================
# TEST CLASS
# =========================
cat <<EOF > $BASE/classes/AppointmentServiceTest.cls
@isTest
public class AppointmentServiceTest {

    @isTest
    static void testFlow() {

        Patient__c p = new Patient__c(Name='P');
        insert p;

        Doctor__c d = new Doctor__c(Name='D', Availability__c=true);
        insert d;

        Test.startTest();

        Appointment__c a = AppointmentService.createAppointment(
            p.Id,
            d.Id,
            System.now().addDays(1)
        );

        Test.stopTest();

        System.assertNotEquals(null, a.Id);
    }
}
EOF

# =========================
# DEPLOY
# =========================
echo "📦 Deploying..."
sf project deploy start --source-dir force-app --target-org $ORG

echo "🧪 Running tests..."
sf apex run test --result-format human --wait 20 --target-org $ORG

echo "✅ ENTERPRISE SETUP COMPLETE!"
