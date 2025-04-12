import React, { useState } from 'react';

// Define types for better TypeScript support
interface GestureInfo {
  image: string;
  description: string;
}

interface SensorData {
  index: number;
  middle: number;
  ring: number;
  pinky: number;
}

interface HistoryItem {
  word: string;
  timestamp: string;
}

// Mock data for testing - replace with actual Bluetooth connection
const mockGestures = {
  "hello": { image: "hello.png", description: "Hand open, fingers spread" },
  "thanks": { image: "thanks.png", description: "Hand to chest" },
  "help": { image: "help.png", description: "Fist with thumb up" },
  "yes": { image: "yes.png", description: "Nodding motion" },
  "no": { image: "no.png", description: "Shaking motion" }
};

function App() {
  const [connected, setConnected] = useState(false);
  const [currentWord, setCurrentWord] = useState("");
  const [currentGesture, setCurrentGesture] = useState(null);
  const [sensorData, setSensorData] = useState({
    index: 0,
    middle: 0,
    ring: 0,
    pinky: 0
  });
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showAbout, setShowAbout] = useState(false);

  // Connect to the Arduino glove via Bluetooth
  const connectToGlove = () => {
    console.log("Connecting to glove...");
    
    setTimeout(() => {
      setConnected(true);
      console.log("Connected to glove!");
      
      startMockDataStream();
    }, 1500);
  };

  const startMockDataStream = () => {
    const interval = setInterval(() => {
      const newSensorData = {
        index: Math.floor(Math.random() * 1024),
        middle: Math.floor(Math.random() * 1024),
        ring: Math.floor(Math.random() * 1024),
        pinky: Math.floor(Math.random() * 1024)
      };
      
      setSensorData(newSensorData);
      
      if (Math.random() > 0.8) {
        const words = Object.keys(mockGestures);
        const randomWord = words[Math.floor(Math.random() * words.length)];
        processRecognizedWord(randomWord);
      }
    }, 500);
    
    return () => clearInterval(interval);
  };
  
  const processRecognizedWord = (word) => {
    if (!word) return;
    
    setCurrentWord(word);
    setCurrentGesture(mockGestures[word]);
    
    const timestamp = new Date().toLocaleTimeString();
    setHistory(prev => [...prev, { word, timestamp }]);
  };
  
  const speakWord = () => {
    if (!currentWord) return;
    
    const speech = new SpeechSynthesisUtterance(currentWord);
    speech.lang = 'en-US';
    speech.rate = 1.0;
    speech.pitch = 1.0;
    
    window.speechSynthesis.speak(speech);
  };
  
  const handleBluetoothData = (data) => {
    const parts = data.split(',');
    const newSensorData = { ...sensorData };
    let recognizedWord = "";
    
    parts.forEach(part => {
      const [key, value] = part.split(':');
      if (key === 'WORD') {
        recognizedWord = value;
      } else if (key === 'I') {
        newSensorData.index = parseInt(value);
      } else if (key === 'M') {
        newSensorData.middle = parseInt(value);
      } else if (key === 'R') {
        newSensorData.ring = parseInt(value);
      } else if (key === 'P') {
        newSensorData.pinky = parseInt(value);
      }
    });
    
    setSensorData(newSensorData);
    
    if (recognizedWord) {
      processRecognizedWord(recognizedWord);
    }
  };
  
  const getSensorWidth = (value) => {
    return `${(value / 1023) * 100}%`;
  };

  const resetConnection = () => {
    setConnected(false);
    setShowHistory(false);
    setCurrentWord("");
    setCurrentGesture(null);
    setSensorData({
      index: 0,
      middle: 0,
      ring: 0,
      pinky: 0
    });
  };

  // About Us Content
  if (showAbout) {
    return (
      <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#FFF2D7' }}>
        <header className="shadow-sm" style={{ backgroundColor: '#FFF2D7' }}>
          <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <span className="text-xl font-semibold text-gray-900">SignSpeak</span>
            <button 
              onClick={() => setShowAbout(false)}
              className="text-sm font-medium text-gray-900 hover:text-gray-700"
            >
              Back to Home
            </button>
          </nav>
        </header>
        <main className="flex-1 flex flex-col items-center py-12">
          <div className="w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="bg-white shadow overflow-hidden rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h2 className="text-3xl font-bold text-gray-900 mb-4">About SignSpeak</h2>
                <p className="text-lg text-gray-700 mb-6">
                  SignSpeak is an innovative project that bridges the communication gap between the deaf community and others through advanced gesture recognition technology.
                </p>
                <p className="text-lg text-gray-700 mb-6">
                  Our smart glove technology translates sign language gestures into spoken words in real-time, making communication more accessible and inclusive for everyone.
                </p>
                <p className="text-lg text-gray-700">
                  We believe in a world where language barriers don't exist, and we're working to make that vision a reality.
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#FFF2D7' }}>
      <header className="shadow-sm" style={{ backgroundColor: '#FFF2D7' }}>
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <span className="text-xl font-semibold text-gray-900">SignSpeak</span>
          <div className="flex items-center space-x-4">
            {connected && (
              <>
                <button 
                  onClick={() => setShowHistory(!showHistory)}
                  className="text-sm font-medium text-gray-900 hover:text-gray-700"
                >
                  {showHistory ? 'Hide History' : 'Show History'}
                </button>
                <button 
                  onClick={resetConnection}
                  className="text-sm font-medium text-gray-900 hover:text-gray-700"
                >
                  Back to Home
                </button>
              </>
            )}
            <button 
              onClick={() => setShowAbout(true)}
              className="text-sm font-medium text-gray-900 hover:text-gray-700"
            >
              About Us
            </button>
          </div>
        </nav>
      </header>
      
      <main className="flex-1 flex flex-col items-center">
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {!connected ? (
            <div className="text-center py-12">
              <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl">
                Welcome to SignSpeak
              </h1>
              <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl">
                Connect your gesture recognition glove to start translating sign language
              </p>
              <div className="mt-5 max-w-md mx-auto flex justify-center md:mt-8">
                <div className="rounded-md shadow">
                  <button
                    onClick={connectToGlove}
                    className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-black hover:bg-gray-800 md:py-4 md:text-lg md:px-10"
                  >
                    Connect Glove
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-8">
              {!showHistory ? (
                <div className="bg-white shadow overflow-hidden rounded-lg">
                  <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
                    <div>
                      <h3 className="text-lg leading-6 font-medium text-gray-900">
                        Gesture Recognition
                      </h3>
                      <p className="mt-1 max-w-2xl text-sm text-gray-500">
                        Real-time sign language translation
                      </p>
                    </div>
                    <div className="rounded-md shadow">
                      <button
                        onClick={speakWord}
                        disabled={!currentWord}
                        className={`flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white ${currentWord ? 'bg-black hover:bg-gray-800' : 'bg-gray-300'}`}
                      >
                        Speak Word
                      </button>
                    </div>
                  </div>
                  
                  <div className="border-t border-gray-200">
                    <div className="bg-gray-50 px-4 py-5 sm:p-6">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-gray-900 uppercase">
                          {currentWord || "Awaiting Gesture..."}
                        </div>
                        {currentGesture && (
                          <div className="mt-2 text-sm text-gray-500">
                            {currentGesture.description}
                          </div>
                        )}
                      </div>
                      
                      <div className="mt-8 flex flex-col items-center">
                        <div className="w-48 h-48 bg-gray-200 rounded-lg flex items-center justify-center mb-4">
                          {currentGesture ? (
                            <img 
                              src={`/images/${currentGesture.image}`} 
                              alt={currentWord}
                              className="max-w-full max-h-full"
                            />
                          ) : (
                            <span className="text-gray-400">Gesture Image</span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="px-4 py-5 sm:p-6">
                      <h4 className="text-base font-medium text-gray-900 mb-4">Sensor Readings</h4>
                      
                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-500">Index</span>
                            <span className="text-sm text-gray-900">{sensorData.index}</span>
                          </div>
                          <div className="mt-1 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-black rounded-full h-2"
                              style={{ width: getSensorWidth(sensorData.index) }}
                            ></div>
                          </div>
                        </div>
                        
                        <div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-500">Middle</span>
                            <span className="text-sm text-gray-900">{sensorData.middle}</span>
                          </div>
                          <div className="mt-1 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-black rounded-full h-2"
                              style={{ width: getSensorWidth(sensorData.middle) }}
                            ></div>
                          </div>
                        </div>
                        
                        <div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-500">Ring</span>
                            <span className="text-sm text-gray-900">{sensorData.ring}</span>
                          </div>
                          <div className="mt-1 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-black rounded-full h-2"
                              style={{ width: getSensorWidth(sensorData.ring) }}
                            ></div>
                          </div>
                        </div>
                        
                        <div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-500">Pinky</span>
                            <span className="text-sm text-gray-900">{sensorData.pinky}</span>
                          </div>
                          <div className="mt-1 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-black rounded-full h-2"
                              style={{ width: getSensorWidth(sensorData.pinky) }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white shadow overflow-hidden rounded-lg">
                  <div className="px-4 py-5 sm:px-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Gesture History
                    </h3>
                    <p className="mt-1 max-w-2xl text-sm text-gray-500">
                      Record of recognized gestures
                    </p>
                  </div>
                  
                  <div className="border-t border-gray-200">
                    {history.length > 0 ? (
                      <ul className="divide-y divide-gray-200">
                        {history.map((item, index) => (
                          <li key={index} className="px-4 py-4 sm:px-6">
                            <div className="flex items-center justify-between">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {item.word}
                              </p>
                              <div className="ml-2 flex-shrink-0 flex">
                                <p className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                                  {item.timestamp}
                                </p>
                              </div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="px-4 py-5 sm:p-6 text-center text-gray-500">
                        No gestures recognized yet
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;