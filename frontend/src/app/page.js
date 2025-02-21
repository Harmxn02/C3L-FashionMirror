"use client";
import { useRef, useState } from "react";

export default function Home() {
	const videoRef = useRef(null);
	const canvasRef = useRef(null);
	const [result, setResult] = useState(null);
	const [loading, setLoading] = useState(false);

	const startCamera = async () => {
		try {
			const stream = await navigator.mediaDevices.getUserMedia({
				video: { facingMode: "user" }, // Try "user" for front camera
			});
	
			if (videoRef.current) {
				videoRef.current.srcObject = stream;
				videoRef.current.play();
			}
		} catch (error) {
			console.error("Camera access error:", error);
		}
	};
	

	const captureImage = async () => {
		if (!canvasRef.current || !videoRef.current) return;
	
		const canvas = canvasRef.current;
		const video = videoRef.current;
	
		canvas.width = video.videoWidth;
		canvas.height = video.videoHeight;
		const ctx = canvas.getContext("2d");
	
		ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
	
		// Log pixel data to check if it's all black
		const pixelData = ctx.getImageData(0, 0, 1, 1).data;
		console.log("First pixel data:", pixelData);
	
		canvas.toBlob(sendToBackend, "image/jpeg");
	};
	

	const sendToBackend = async (blob) => {
		setLoading(true);
		const formData = new FormData();
		formData.append("file", blob, "image.jpg");

		try {
			const response = await fetch("http://localhost:8000/detect", {
				method: "POST",
				body: formData,
			});

			const data = await response.json();
			setResult(data.detected);
		} catch (error) {
			console.error("Error:", error);
			setResult("Error detecting colors");
		}
		setLoading(false);
	};

	return (
		<div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white p-4">
			<h1 className="text-2xl font-bold mb-4">Hair & Clothing Color Detection</h1>

			<video
				ref={videoRef}
				autoPlay
				playsInline
				muted
				className="border-2 border-gray-300 rounded-lg w-full h-auto max-w-md aspect-video bg-black"
			/>
			<canvas ref={canvasRef} className="hidden" />

			<div className="flex space-x-4 mt-4">
				<button onClick={startCamera} className="px-4 py-2 bg-blue-500 hover:bg-blue-700 text-white rounded">
					Start Camera
				</button>
				<button onClick={captureImage} className="px-4 py-2 bg-green-500 hover:bg-green-700 text-white rounded">
					Capture Image
				</button>
			</div>

			{loading && <p className="mt-4 text-yellow-400">Processing...</p>}
			{result && <p className="mt-4 text-green-300">Detected: {result}</p>}
		</div>
	);
}
