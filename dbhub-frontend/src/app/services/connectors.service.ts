import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ConnectorsService {

  private apiUrl = 'http://127.0.0.1:8000/connectors';

  constructor(private http: HttpClient) {}

  getConnectors() {
    return this.http.get<any[]>(this.apiUrl);
  }

  addConnector(connector: any) {
    return this.http.post(this.apiUrl, connector);
  }

  deleteConnector(index: number) {
    return this.http.delete(
      `${this.apiUrl}/${index}`
    );
  }

}