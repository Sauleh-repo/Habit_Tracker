// src/services/api.js

import axios from 'axios';

const apiClient = axios.create({
    baseURL:'http://habit-tracker-prod.eba-8xdmc2ph.ap-south-1.elasticbeanstalk.com',
});

apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

apiClient.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        if (error.response && error.response.status === 401) {
            console.log('Token expired or invalid, logging out.');
            localStorage.removeItem('token');
            window.location.reload();
        }
        return Promise.reject(error);
    }
);

// --- User Functions ---
export const register = (username, password) => {
    return apiClient.post('/users/register', { username, password });
};

export const login = (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    return apiClient.post('/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
};

// --- Habit Functions ---
export const getHabits = () => {
    return apiClient.get('/habits/');
};

export const createHabit = (name, description) => {
    return apiClient.post('/habits/', { name, description });
};

export const toggleHabitCompletion = (habitId) => {
    return apiClient.put(`/habits/${habitId}/toggle`);
};

export const deleteHabit = (habitId) => {
    return apiClient.delete(`/habits/${habitId}`);
};

// --- ADD THIS NEW FUNCTION ---
// It takes the habit's ID and an object with the new name and/or description
export const updateHabit = (habitId, { name, description }) => {
    return apiClient.put(`/habits/${habitId}`, { name, description });
};