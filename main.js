let serialportgsm = require('serialport-gsm')

serialportgsm.list((err, result) => {
    console.log(result)
})

let modem = serialportgsm.Modem()
let options = {
    baudRate: 9600,
    dataBits: 8,
    stopBits: 1,
    parity: 'none',
    rtscts: false,
    xon: false,
    xoff: false,
    xany: false,
    autoDeleteOnReceive: false,
    enableConcatenation: true,
    incomingCallIndication: true,
    incomingSMSIndication: true,
    pin: '',
    customInitCommand: '',
    logger: console
}

modem.open('COM8', options, (data)=>{
    console.log('COM8', data)
});

// modem.on('open', data => {
//     // modem.setModemMode(callback, 'PDU')
//     modem.initializeModem((data)=>{
//         console.log('modem initialized')
//         modem.sendSMS('99363489374', 'Salam modemdan!', true, (data)=>{
//             console.log(data)
//         })
//
//     })
//
// })


// modem.on('onSendingMessage', result => {
//     console.log(result.status)
// })


modem.getOwnNumber((data)=>{
    console.log('own number', data)})

console.log('Exit from modem')
modem.close()


// modem.on('onSendingMessage', result => {
//     console.log(result.status)
// })


