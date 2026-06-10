import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class DashboardService {

  private apiUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  getStats() {
    return this.http.get<any>(
      `${this.apiUrl}/dashboard-stats`
    );
  }

}