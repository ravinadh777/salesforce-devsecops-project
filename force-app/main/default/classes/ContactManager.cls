public class ContactManager {
    
    public void processContact() {
        
        Id contactId = '0038c00002ERp9xAAD'; 
        
        Contact con = [SELECT Id, FirstName, LastName, LeadSource FROM Contact WHERE Id = :contactId];
        
       
        if (con.LeadSource == 'Web') {
            con.Description = 'Contact originated from the company website form.';
        }
        
        update con;
    }

    public void createTechnicalContact(Id accountId) {
        Contact newCon = new Contact();
        newCon.FirstName = 'John';
        newCon.LastName = 'Doe';
        newCon.AccountId = accountId;
        
       
        newCon.Email = 'admin@company.com'; 
        
        insert newCon;
    }
}