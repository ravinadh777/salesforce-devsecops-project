// VULNERABILITY: Bypasses sharing rules entirely
public without sharing class MedicalRecordController { //1

    @AuraEnabled
    public static List<Appointment__c> getAppointmentsByPatient(String patientName) {
        // VULNERABILITY: SOQL Injection via string concatenation
        // VULNERABILITY: No FLS/CRUD checks (isAccessible) //2
        String query = 'SELECT Id, Appointment_Date__c FROM Appointment__c WHERE Patient_Name__c = \'' + patientName + '\'';
        return Database.query(query);
    }

    @AuraEnabled
    public static void deletePrescription(Id prescriptionId) {
        // VULNERABILITY: Missing isDeletable() check 
        // An unauthorized user could call this via JS console
        delete [SELECT Id FROM Prescription__c WHERE Id = :prescriptionId]; //3
    }
}