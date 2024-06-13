import React, { useState, useEffect } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import './TTSAvatar.css';

axios.defaults.baseURL = 'http://localhost:5001';
const socket = io('http://localhost:5001');

const TTSAvatar = () => {
    const [avatar, setAvatar] = useState('');
    const [message, setMessage] = useState('');
    const [messageAmplitudes, setMessageAmplitudes] = useState([])
    const [guest, setGuest] = useState('');

    useEffect(() => {
        // Fetch a random avatar from the avatars directory
        const fetchAvatar = async () => {
            try {
                if (guest) {
                    const response = await axios.get('/api/random_avatar');
                    setAvatar('http://localhost:5001' + response.data.avatar);
                }
            } catch (error) {
                console.error('Error fetching avatar:', error);
            }
        };

        fetchAvatar();
    }, [guest]);

    useEffect(() => {
        // Set up WebSocket listeners
        socket.on('guest_update', (data) => {
            setGuest(data.guest);
            if (data.guest) {
                fetchGuestMessage(data.guest);
            } else {
                setMessage('');
            }
        });

        socket.on('message_update', (data) => {
            setMessage(data.message);
            setMessageAmplitudes(data.amplitudes || [])
        });

        socket.on('guest_clear', () => {
            setGuest('');
            setMessage('');
            setMessageAmplitudes([]);
            setAvatar('');
        })

        return () => {
            // Clean up WebSocket listeners on component unmount
            socket.off('guest_update');
            socket.off('message_update');
            socket.off('guest_clear');
        };
    }, [guest]);

    useEffect(() => {
        if (messageAmplitudes && messageAmplitudes.length > 0) {
            generateKeyframes(messageAmplitudes);
        } else {
            const avatar_element = document.querySelector('.avatar-image');
            if (avatar_element) {
                avatar_element.style.animation = '';
            }
        }
    }, [messageAmplitudes])

    const generateKeyframes = (amplitudes) => {
        const sample_rate = 22050;
        const duration = amplitudes.length / sample_rate;
        console.log(amplitudes.length)
        const sample_factor = Math.floor(amplitudes.length / 200);
        const sampled_amplitudes = amplitudes.filter((_, index) => index % sample_factor === 0);

        const keyframes = sampled_amplitudes.map((amp, index) => {
            const percentage = Math.ceil((index / sampled_amplitudes.length) * 100);
            const translateY = amp * 48;
            return `${percentage}% { transform: translateY(-${translateY}px); }`;
        }).join('\n');
        const stylesheet = document.styleSheets[0];
        const animation_name = 'avatarBounceAnimation';
        const keyframesRule = `@keyframes ${animation_name} { ${keyframes} }`;

        for (let i = stylesheet.cssRules.length - 1; i >= 0; i--) {
            if (stylesheet.cssRules[i].name === animation_name) {
                stylesheet.deleteRule(i);
            }
        }

        stylesheet.insertRule(keyframesRule, stylesheet.cssRules.length)

        const avatar_element = document.querySelector('.avatar-image');
        if (avatar_element)
            avatar_element.style.animation = `${animation_name} ${duration}s linear`
    }

    const handlePickGuest = async () => {
        try {
            const response = await axios.post('/api/pick_guest');
            setGuest(response.data.guest);
        } catch (error) {
            console.error('Error picking guest:', error);
        }
    };

    const handleClearGuest = async () => {
        try {
            await axios.post('/api/clear_guest');
            setGuest('');
            setMessage('');
            setAvatar('');
        } catch (error) {
            console.error('Error clearing guest:', error);
        }
    };

    const handleGuestSubmit = async (e) => {
        if (e.key === 'Enter') {
            try {
                const response = await axios.post('/api/set_guest', { guest: e.target.value });
                setGuest(response.data.guest);
                
                e.target.value = ''; // Clear the input field after submitting
            } catch (error) {
                console.error('Error setting guest:', error);
            }
        }
    };

    const fetchGuestMessage = async (guestName) => {
        try {
            const response = await axios.get(`/api/get_guest_message?guest=${guestName}`);
            setMessage(response.data.message);
        } catch (error) {
            console.error('Error fetching guest message:', error);
        }
    };

    const animatedMessage = message.split(' ').map((word, wordIndex) => (
      <span key={wordIndex} className="animated-word">
          {word.split('').map((char, charIndex) => (
              <span 
                  key={charIndex} 
                  className="animated-letter" 
                  style={{ animationDelay: `${(wordIndex * 0.5) + (charIndex / word.length * 0.5)}s` }} // Add a delay for each letter
              >
                  {char}
              </span>
          ))}
          {'\u00A0'}
      </span>
    ));

    return (
        <div className="tts-avatar-container">
            <div className="avatar-box">
                {avatar && <img src={avatar} alt="TTS Avatar" className="avatar-image" />}
                {message !== "" && <div className="guest-message"><span className="guest-name">{guest}</span><br />{animatedMessage}</div>}
            </div>
            <div className="controls">
                <button onClick={handlePickGuest}>Pick Guest</button>
                <input
                    type="text"
                    onKeyPress={handleGuestSubmit}
                    placeholder={guest ? guest : 'Enter guest name'}
                />
                <button onClick={handleClearGuest}>Clear Guest</button>
            </div>
        </div>
    );
};

export default TTSAvatar;
