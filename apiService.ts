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

// Adding a simple generic cache interface
interface Cache<T> {
    [key: string]: T;
}

class ApiServiceSingleton {
    private static instance: ApiServiceSingleton;
    private noteCache: Cache<ApiResponse<Note[]>> = {}; // Cache for storing notes by User ID

    private constructor() {}

    static getInstance(): ApiServiceSingleton {
        if (!ApiServiceSingleton.instance) {
            ApiServiceSingleton.instance = new ApiServiceSingleton();
        }
        return ApiServiceSingleton.instance;
    }

    async loginUser(userData: User): Promise<ApiResponse<User>> {
        try {
            const response = await axios.post<ApiResponse<User>>(`${API_USER_ENDPOINT}/login`, userData);
            this.logToConsole(`User Login: ${userData.username}`);
            return response.data;
        } catch (error) {
            throw new Error('Failed to login user.');
        }
    }

    async registerUser(userData: User): Promise<ApiResponse<User>> {
        try {
            const response = await axios.post<ApiResponse<User>>(`${API_USER_ENDPOINT}/register`, userData);
            this.logToConsole(`User Registration: ${userData.username}`);
            return response.data;
        } catch (error) {
            throw new Error('Failed to register user.');
        }
    }

    async createNote(noteData: Note): Promise<ApiResponse<Note>> {
        try {
            const response = await axios.post<ApiResponse<Note>>(`${API_NOTE_ENDPOINT}/create`, noteData);
            // Invalidate cache for the user when a new note is created
            delete this.noteCache[`user_${noteData.userId}`];
            this.logToConsole(`Note Creation: ${noteData.title}`);
            return response.data;
        } catch (error) {
            throw new Error('Failed to create note.');
        }
    }

    async getAllNotesByUser(userId: number): Promise<ApiResponse<Note[]>> {
        const cacheKey = `user_${userId}`;
        if (this.noteCache[cacheKey]) {
            this.logToConsole(`Fetching Notes for User ID from Cache: ${userId}`);
            return this.noteCache[cacheKey];
        }
        try {
            const response = await axios.get<ApiResponse<Note[]>>(`${API_NOTE_ENDPOINT}/user/${userId}`);
            this.noteCache[cacheKey] = response.data; // Cache the result
            this.logToConsole(`Fetching Notes for User ID: ${userId}`);
            return response.data;
        } catch (error) {
            throw new Error('Failed to get notes.');
        }
    }

    async updateNote(noteData: Note): Promise<ApiResponse<Note>> {
        if (!noteData.id) throw new Error('Note ID is required for update.');
        try {
            const response = await axios.put<ApiResponse<Note>>(`${API_NOTE_ENDPOINT}/update/${noteData.id}`, noteData);
            // Invalidate cache for the user when a note is updated
            delete this.noteCache[`user_${noteData.userId}`];
            this.logToConsole(`Note Update: ${noteData.id}`);
            return response.data;
        } catch(error) {
            throw new Error('Failed to update note.');
        }
    }

    async deleteNote(noteId: number): Promise<ApiResponse<{}>> {
        try {
            // To invalidate the cached notes for the user, you may need to fetch the note first to get the userId if not provided directly,
            // or implement another logic that helps to identify the associated user ID.
            const response = await axios.delete<ApiResponse<{}>>(`${API_NOTE_ENDPOINT}/delete/${noteId}`);
            // Assuming userId is somehow retrieved before or you extend this functionality
            // delete this.noteCache[`user_${userId}`];
            this.logToConsole(`Note Deletion: ${noteId}`);
            return response.data;
        } catch (error) {
            throw new Error('Failed to delete note.');
        }
    }

    private logToConsole(message: string): void {
        console.log(`[NoteVault ApiService]: ${message}`);
    }
}

const ApiService = ApiServiceSingleton.getInstance();
export default ApiService;