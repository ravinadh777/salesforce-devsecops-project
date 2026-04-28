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
