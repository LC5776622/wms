function updateClock(){
    var now = new Date();
    var date = now.getDate();
    var month = now.getMonth()+1;
    var year = now.getFullYear();
    var hours = now.getHours();
    var minutes = now.getMinutes();
    var seconds = now.getSeconds();
    var timeString = 
                    date.toString().padStart(2, '0') + '-' +
                    month.toString().padStart(2, '0') + '-' +
                    year.toString().padStart(4,'0') + ' ' +
                    hours.toString().padStart(2, '0') + ':' +
                    minutes.toString().padStart(2, '0') + ':' +
                    seconds.toString().padStart(2, '0');
    document.getElementById('clock').innerHTML=timeString
}
setInterval(updateClock, 1000);js