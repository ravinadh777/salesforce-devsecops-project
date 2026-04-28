trigger AccountTrigger on Account (before insert) {
    for (Account acc : Trigger.new) {
		if (acc.Name != null && acc.Name.contains('Test')) {
        	  system.debug('Account name cannot contain the word "Test".');
   		}
    }
}