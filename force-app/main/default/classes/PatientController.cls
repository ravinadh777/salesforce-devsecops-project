public class PatientController {
    @AuraEnabled
    public static List<Patient__c> getPatients() {
        // VULNERABILITY: No check to see if the user has permission 
        // to see the Patient object or the SSN field.
        return [SELECT Name, SSN__c FROM Patient__c]; //WITH USER_MODE
    }
}