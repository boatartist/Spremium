if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js')
      .then(registration => console.log('Service Worker registered'))
      .catch(error => 'SW registration failed');
}

document.getElementById('audio_source').preload = 'metadata';
//audioPlayerForm = document.forms['audio_data'];
try {
  document.getElementById('audio_source').currentTime = document.cookie.split(';')[0].split('=')[1];}
catch(error) {
  console.log(`some sort of error setting player currentTime on load: ${error}`)
  document.getElementById('audio_source').currentTime = 0;
}
document.getElementById('audio_source').addEventListener("ended", nextSong);
//chrome.webRequest.onBeforeRedirect.addListener(sendAudioUpdate);
let timestampInterval;

function showNavBar(){
  document.getElementById('navbar').style.display = 'block';
  user_id = document.getElementById('user_id');
  if (user_id.textContent.length > 0){
    document.getElementById('logout').style.display = 'block';
    document.getElementById('account').style.display = 'block';
    document.getElementById('logged_as').style.display = 'block';
    document.getElementById('login').style.display = 'none';
    document.getElementById('register').style.display = 'none';
  }
  else {
    document.getElementById('account').style.display = 'none';
    document.getElementById('logged_as').style.display = 'none';
    document.getElementById('logout').style.display = 'none';
    document.getElementById('login').style.display = 'block';
    document.getElementById('register').style.display = 'block';
  }

  is_admin = document.getElementById('is_admin');
  if (is_admin.textContent == 1){
    document.getElementById('admin').style.display = 'block';
  }
  else {
    document.getElementById('admin').style.display = 'none';
  }
}

function hideNavBar(){
  document.getElementById('navbar').style.display = 'none';
  document.getElementById('logout').style.display = 'none';
  document.getElementById('account').style.display = 'none';
  document.getElementById('login').style.display = 'none';
  document.getElementById('register').style.display = 'none';
  document.getElementById('admin').style.display = 'none';
  document.getElementById('logged_as').style.display = 'none';
}

function swapPlay(){
  playButton = document.getElementById('playbutton');
  if (playButton.value == 'paused'){
    document.getElementById('audio_source').play();
    playButton.classList.remove("fa-play");
    playButton.classList.add('fa-pause');
    playButton.value = 'playing';
    if (!timestampInterval){
      document.getElementById('timeslider').max = document.getElementById('audio_source').duration;
      timestampInterval = setInterval(updateTimestamp, 500);}
    }
  else {
    document.getElementById('audio_source').pause();
    playButton.classList.remove("fa-pause");
    playButton.classList.add('fa-play');
    playButton.value = 'paused';
    clearInterval(timestampInterval);
    timestampInterval = null;}
}

function updateTimestamp(){
  timestamp = document.getElementById('timestamp');
  length = document.getElementById('audio_source').duration;
  document.getElementById('timeslider').value = timestamp;
  console.log(document.getElementById('timeslider').value);
  timestamp.textContent = timestampFormat(document.getElementById('audio_source').currentTime) +' / ' + timestampFormat(length);
  document.cookie = 'current_time='+document.getElementById('audio_source').currentTime +';path=/';
}

function restartSong(){
  console.log('restarting');
  document.getElementById('audio_source').currentTime = 0;
  document.cookie = 'current_time=0;path="/"';
  updateTimestamp();
}

function timestampFormat(num){
  formatted = `${String(Math.floor(num/60)).padStart(2, '0')}:${String(Math.round(num-60*Math.floor(num/60))).padStart(2, '0')}`;
  return formatted;
}

Number.prototype.pad = function(size) {
    var s = String(this);
    while (s.length < (size || 2)) {s = "0" + s;}
    return s;
}

function startAlbum(){
  albumForm = document.getElementById('songsToAdd');
  document.cookie = 'current_time=0;path="/";';
  albumForm.submit();
}

function startAlbumLater(){
  albumLaterForm = document.getElementById('songsToAddLater');
  albumLaterForm.submit();
}

function nextSong(){
  document.cookie = 'current_time=0;path="/";';
  window.location.replace('/nextSong');
}

function deleteFromQueue(index){
  document.getElementById('songIndex').value = index;
  deleteForm = document.getElementById('deleteThisSong');
  deleteForm.submit();
}

//shuffle array to get a random song from the random genres function (as it still searches by genre so we can't just pick a random index)
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

function random_genre(){
  genreList = Array.from(document.querySelectorAll('[id=rand_genre]'));
  num = Math.floor(Math.random() * (genreList.length));
  genre = genreList[num].innerText;
  document.getElementById('genre_name').innerHTML = genre;
  document.getElementById('genre_name_2').innerHTML = genre;
  document.getElementById('example_song').style.visibility = 'visible';
  document.getElementById('genre_image').src = '/static/images/jack_russell_'+genre+'.svg';
  songsList = Array.from(document.querySelectorAll('[id=genred_song]'));
  shuffleArray(songsList);
  console.log(songsList);
  for (var i=0; i<songsList.length; i++) {
    console.log(songsList[i].children[0]);
    if (songsList[i].children[0].innerText == genre) {
      songName = songsList[i].children[1].innerText;
      songId = songsList[i].children[2].innerText;
      console.log(songName);
      document.getElementById('example_song_name').innerHTML = `<a href="song/${songId}">${songName}</a>`;
    }
  }
}

document.getElementById('audio_source').onloadeddata = function() {
  console.log('setting the time?');
  console.log(document.cookie);
  document.getElementById('audio_source').currentTime = document.cookie.split(';')[0].split('=')[1]; //document.getElementById('start_time').value;
  console.log('set time');
  console.log(document.cookie.split(';')[0].split('=')[1]);
}


document.getElementById('audio_source').oncanplaythrough = function() {
    document.getElementById('playbutton').click();
    swapPlay();
    console.log('tried playing');
};
