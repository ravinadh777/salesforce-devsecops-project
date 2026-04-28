trigger AppointmentTrigger on Appointment__c (before insert, before update) {

    for (Appointment__c a : Trigger.new) {
        if (a.Appointment_Date__c != null && a.Appointment_Date__c < System.now()) {
            a.addError('Appointment date cannot be in the past');
        }
        if (String.isBlank(a.Status__c)) {
            a.Status__c = 'Scheduled';
        }
    }
}