import datetime
import logging
import time

from gsmmodem.modem import Sms
from serial.tools import list_ports
from pprint import pprint
from gsmmodem import GsmModem
import sys

from serial import SerialException

from gsmmodem.exceptions import TimeoutException, CommandError, InterruptedException

log = logging.getLogger(__name__)


class Modem:
    __slots__ = ('modem',)

    def __init__(self, device, rate, *args, **kwargs):
        self.modem = GsmModem(device, rate)

        super().__init__(*args, **kwargs)

    def own_number(self, ):
        print('Initializing modem...')
        # Uncomment the following line to see what the modem is doing:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
        modem = self.modem
        modem.connect()
        number = modem.ownNumber
        # number = modem.write('AT+CNUM')
        print(number)
        modem.close()
        return number

    def send_sms_at(self, message, recipient):
        """Send SMS via local modem with AT commands
        Meact configuration:
        action_config = {
          "recipient": ["your-number", "your-number2'],
          "port": "/dev/ttyUSB1",
          "speed": 19200,
          "enabled": 1
        }
        """

        print('Sending SMS via AT')

        # logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
        modem = self.modem

        while True:
            try:
                modem.connect()
                modem.waitForNetworkCoverage()
            except TimeoutException:
                pass
            else:
                break
        result = []
        for rcpt in recipient:
            try:
                sms = modem.sendSms(rcpt, message)
                print('Send sms result:', sms.__dict__)
                result.append(sms.__dict__)

            except TimeoutException:
                print('Got exception in send_sms_at')
                sys.exit(2)
        modem.close()
        return result

    def call_to(self, number):
        if number == None or number == '00000':
            print('Error: Please change the NUMBER variable\'s value before running this example.')
            sys.exit(1)
        print('Initializing modem...')
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
        modem = self.modem

        modem.connect()
        print('Waiting for network coverage...')
        modem.waitForNetworkCoverage(30)
        print('Dialing number: {0}'.format(number))
        call = modem.dial(number)
        print('Waiting for call to be answered/rejected')
        was_answered = False
        while call.active:
            if call.answered:
                was_answered = True
                print('Call has been answered; waiting a while...')
                # Wait for a bit - some older modems struggle to send DTMF tone immediately after answering a call
                time.sleep(3.0)
                print('Playing DTMF tones...')
                try:
                    if call.active:  # Call could have been ended by remote party while we waited in the time.sleep() call
                        call.sendDtmfTone('9515999955951')
                except InterruptedException as e:
                    # Call was ended during playback
                    print('DTMF playback interrupted: {0} ({1} Error {2})'.format(e, e.cause.type, e.cause.code))
                except CommandError as e:
                    print('DTMF playback failed: {0}'.format(e))
                finally:
                    if call.active:  # Call is still active
                        print('Hanging up call...')
                        call.hangup()
                    else:  # Call is no longer active (remote party ended it)
                        print('Call has been ended by remote party')
            else:
                # Wait a bit and check again
                time.sleep(0.5)
        if not was_answered:
            print('Call was not answered by remote party')
        print('Done.')
        modem.close()

    @staticmethod
    def autodetect_modem(pin=None, check_fn=None, modem_options=None):
        """ Autodetect a suitable cellular modem connected to the system.

        :param pin: Security PIN to unlock the SIM.
        :param check_fn: Callable that should take a single ``modem`` argument
            and return True if the modem instance is suitable.
        :param modem_options: Structure to pass as keyword arguments to
            ``GsmModem`` initialisation.
        :type modem_options: dict-like
        :returns: Connected modem instance
        :rtype: :class:`gsmmodem.modem.GsmModem`

        This method will iterate through all potential serial ports on the system
        and attempt to ``connect()`` to each of them in turn.  The first serial
        port that connects successfully, and passes the ``check_fn(modem)`` call
        (if ``check_fn`` is specified), will be returned.

        All other unsuccessful connections will be closed during the process.

        This method will return ``None`` if no modems could be detected.
        """
        ports = list_ports.comports()
        if not ports:
            log.error('No modem ports detected on system.')
            return

        if modem_options is None:
            modem_options = {'baudrate': 9600}

        modem = None

        for port in ports:
            print(port.__dict__)
            modem = GsmModem(port.device, **modem_options)
            try:
                log.debug('Attempting to connect to modem at %s' % port)
                modem.connect(pin=pin)
                if not check_fn or check_fn and check_fn(modem):
                    log.debug('Successfully detected modem at %s' % port)
                    return modem
            except SerialException:
                log.warning('Serial communication problem for port %s' % port)
            except TimeoutException:
                log.warning('Timeout detected on port %s' % port)

            log.debug('Closing modem at %s' % port)
            modem.close()

    def send_ussd_at(self, ussd_string):
        print('Initializing modem...')
        # logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
        modem = self.modem
        modem.connect()
        modem.waitForNetworkCoverage(10)
        print('Sending USSD string: {0}'.format(ussd_string))
        response = modem.sendUssd(ussd_string)  # response type: gsmmodem.modem.Ussd
        message = response.message
        print('USSD reply received: {0}'.format(message))
        if response.sessionActive:
            print('Closing USSD session.')
            # At this point, you could also reply to the USSD message by using response.reply()
            response.cancel()
        else:
            print('USSD session was ended by network.')
        modem.close()
        return message

    def get_unread_text(self, key: str = '9703BB8D5A'):
        if key.strip() == '9703BB8D5A':
            modem = self.modem

            try:
                print("Connecting mode")
                modem.connect()
            except:
                return "Error connecting"
            try:
                messages = modem.listStoredSms(status=Sms.STATUS_RECEIVED_UNREAD)
            except Exception as e:
                return str(e)

            modem.close()
            print("Got %d messages" % len(messages))
            message_data = []
            for message in messages:
                message_data.append({
                    'number': message.number,
                    'text': message.text,
                    'time': message.time.strftime("%Y-%m-%d %H:%M:%S"),
                    'smsc': message.smsc,

                })
            return message_data
        else:
            return "Incorrect key"

    def get_all_text(self, key: str = '9703BB8D5A'):
        if key.strip() == '9703BB8D5A':
            modem = self.modem

            try:
                print("Connecting modem")
                modem.connect()
            except Exception as e:
                return str(e)

            try:
                messages = modem.listStoredSms()
            except Exception as e:
                return str(e)

            modem.close()
            print("Got %d messages" % len(messages))
            message_data = []
            for message in messages:
                message_data.append({
                    'number': message.number,
                    'text': message.text,
                    'time': message.time.strftime("%Y-%m-%d %H:%M:%S"),
                    'smsc': message.smsc,

                })
            return message_data
        else:
            return "Incorrect key"


if __name__ == '__main__':
    data = {'message': "All sms"}

    detect_modem = Modem.autodetect_modem()

    print(f"Modem port: {detect_modem.port}")
    print(f"Modem baudrate: {detect_modem.baudrate}")

    modem = Modem(device=detect_modem.port, rate=detect_modem.baudrate)

    result = modem.get_all_text()
    pprint(result)
g