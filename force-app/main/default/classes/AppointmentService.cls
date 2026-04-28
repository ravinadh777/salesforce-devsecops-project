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