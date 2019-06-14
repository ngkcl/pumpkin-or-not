let video = document.querySelector('#camera-stream'),
	image = document.querySelector('#snap'),
	start_camera = document.querySelector('#start-camera'),
	controls = document.querySelector('.controls'),
	take_photo_btn = document.querySelector('#take-photo'),
	delete_photo_btn = document.querySelector('#delete-photo'),
	download_photo_btn = document.querySelector('#download-photo'),
	error_message = document.querySelector('#error-message');



navigator.getMedia = ( navigator.getUserMedia ||
	navigator.webkitGetUserMedia ||
	navigator.mozGetUserMedia ||
	navigator.msGetUserMedia);


if(!navigator.getMedia) {
	displayErrorMessage("Your browser doesn't have support for the navigator.getUserMedia interface.");
} else {
	navigator.getMedia(
		{
			video: true
		}, (stream) => {

			video.srcObject = stream;

			video.play();
			video.onplay = () => {
				showVideo();
			};

		}, (err) => {
			displayErrorMessage("There was an error with accessing the camera stream: " + err.name, err);
		}
	);

}


start_camera.addEventListener("click", (e) => {
	e.preventDefault();

	video.play();
	showVideo();
});


take_photo_btn.addEventListener("click", (e) => {
	e.preventDefault();

	var snap = takeSnapshot();
	console.log(snap);

	image.setAttribute('src', snap);

	delete_photo_btn.classList.remove("disabled");
	download_photo_btn.classList.remove("disabled");

	download_photo_btn.href = snap;

	callPredictor(snap);

	video.pause();
});


delete_photo_btn.addEventListener("click", (e) => {
	e.preventDefault();

	image.setAttribute('src', "");
	image.classList.remove("visible");

	delete_photo_btn.classList.add("disabled");
	download_photo_btn.classList.add("disabled");

	video.play();
});



showVideo = () => {
	hideUI();
	video.classList.add("visible");
	controls.classList.add("visible");
}


takeSnapshot = () => {
	var hidden_canvas = document.querySelector('canvas'),
		context = hidden_canvas.getContext('2d');

	var width = video.videoWidth,
		height = video.videoHeight;

	if (width && height) {
		hidden_canvas.width = width;
		hidden_canvas.height = height;

		context.drawImage(video, 0, 0, width, height);

		return hidden_canvas.toDataURL('image/png');
	}
}


displayErrorMessage = (error_msg, error) => {
	error = error || "";
	if(error){
		console.log(error);
	}

	error_message.innerText = error_msg;

	hideUI();
	error_message.classList.add("visible");
}


hideUI = () => {
	controls.classList.remove("visible");
	start_camera.classList.remove("visible");
	video.classList.remove("visible");
	snap.classList.remove("visible");
	error_message.classList.remove("visible");
}

callPredictor = (snap) => {
	url = "http://127.0.0.1:5000/predict";

	let responseDict = undefined
	
	let data = {
		image: snap
	};

	fetch(url, {
		method: "POST", 
		headers: {
			'Content-type': 'application/json'
		},
		body: JSON.stringify(data)
	})
	.then(res => res.json())
	.then(response => {
		console.log(JSON.stringify(response));
		responseDict = JSON.stringify(response);

		handlePredictorResponse(responseDict) 
	})
	.catch(err => console.error(err))
}

handlePredictorResponse = (data) => {
	if(data['pumpkin'] > data['not pumpkin']) {
		alert('Pumpkin');
	} else {
		alert('Not Pumpkin');
	}
}
