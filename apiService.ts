import axios, { AxiosResponse } from 'axios';

const API_BASE_URL: string = process.env.REACT_APP_API_BASE_URL || '';
const API_USER_ENDPOINT: string = `${API_BASE_URL}/users`;
const API_NOTE_ENDPOINT: string = `${API_BASE_URL}/notes`;

interface User {
    id?: number;
    username: string;
    password: string;
}

interface Note {
    id?: number;
    title: string;
    content: string;
    userId: number;
}

interface ApiResponse<T> {
    data: T;
    message: string;
}

class ApiService {
    static loginUser = async (userData: User): Promise<ApiResponse<User>> => {
        try {
            const response: AxiosResponse<ApiResponse<User>> = await axios.post(`${API_USER_ENDPOINT}/login`, userData);
            return response.data;
        } catch (error) {
            throw new Error('Failed to login user.');
        }
    }

    static registerUser = async (userData: User): Promise<ApiResponse<User>> => {
        try {
            const response: AxiosResponse<ApiResponse<User>> = await axios.post(`${API_USER_ENDPOINT}/register`, userData);
            return response.data;
        } catch (error) {
            throw new Error('Failed to register user.');
        }
    }

    static createNote = async (noteData: Note): Promise<ApiResponse<Note>> => {
        try {
            const response: AxiosResponse<ApiResponse<Note>> = await axios.post(`${API_NOTE_ENDPOINT}/create`, noteData);
            return response.data;
        } catch (error) {
            throw new Error('Failed to create note.');
        }
    }

    static getAllNotesByUser = async (userId: number): Promise<ApiResponse<Note[]>> => {
        try {
            const response: AxiosResponse<ApiResponse<Note[]>> = await axios.get(`${API_NOTE_ENDPOINT}/user/${userId}`);
            return response.data;
        } catch (error) {
            throw new Error('Failed to get notes.');
        }
    }

    static updateNote = async (noteData: Note): Promise<ApiResponse<Note>> => {
        if (!noteData.id) throw new Error('Note ID is required for update.');
        try {
            const response: AxiosResponse<ApiResponse<Note>> = await axios.put(`${API_NOTE_ENDPOINT}/update/${noteData.id}`, noteData);
            return response.data;
        } catch(error) {
            throw new Error('Failed to update note.');
        }
    }

    static deleteNote = async (noteId: number): Promise<ApiResponse<{}>> => {
        try {
            const response: AxiosResponse<ApiResponse<{}>> = await axios.delete(`${API_NOTE_ENDPOINT}/delete/${noteId}`);
            return response.data;
        } catch (error) {
            throw new Error('Failed to delete note.');
        }
    }
}

export default ApiService;