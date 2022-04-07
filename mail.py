from exchangelib import Credentials, Account, FileAttachment, EWSDateTime, EWSTimeZone
import configparser

c = configparser.ConfigParser()
cred_dict = c.read('C:\\Users\\igor.i.plotnikov\\setup.cfg')['teradata']

def log_into_account(cred_dict: dict):
    print('Logging in...\n')
    credentials = Credentials(username=cred_dict['user'], password=cred_dict['password'])
    account = Account(cred_dict['mailbox'], credentials=credentials, autodiscover=True)
    return account


if __name__ == '__main__':
    account = log_into_account(cred_dict) 
    print(account)