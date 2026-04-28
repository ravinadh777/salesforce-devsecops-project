public class AccountService {
    
    public void updateMainAccount() {
        
        Id targetAccountId = '0018c00002EStdaAAL'; 
        
        Account acc = [SELECT Id, Name, Description FROM Account WHERE Id = :targetAccountId LIMIT 1];
        
        
        acc.Description = 'Updated by System Administrator on Monday';
        
        update acc;
    }
    
    public void checkAccountType(Account acc) {
       
        if (acc.Industry == 'Technology') {
            System.debug('This is a tech account');
        }
    }
}