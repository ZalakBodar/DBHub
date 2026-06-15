import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  getRole(): string {
    return localStorage.getItem('role') || '';
  }

  isAdmin(): boolean {
    return this.getRole() === 'Admin';
  }

  isDeveloper(): boolean {
    return this.getRole() === 'Developer';
  }

  isViewer(): boolean {
    return this.getRole() === 'Viewer';
  }
}