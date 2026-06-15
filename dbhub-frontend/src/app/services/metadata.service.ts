import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class MetadataService {

  apiUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  getTables() {
    return this.http.get<any[]>(
      `${this.apiUrl}/tables`
    );
  }

  getColumns(tableName: string) {
    return this.http.get<any[]>(
      `${this.apiUrl}/columns/${tableName}`
    );
  }

  getTableData(tableName: string) {
    return this.http.get<any[]>(
      `${this.apiUrl}/data/${tableName}`
    );
  }
  getMetadata(tableName: string) {

  return this.http.get<any[]>(
    `${this.apiUrl}/metadata/${tableName}`
  );

}
getQueryHistory() {
  return this.http.get<any[]>(
    `${this.apiUrl}/query-history`
  );
}
getRelationships() {

  return this.http.get<any[]>(
    `${this.apiUrl}/relationships`
  );

}

  getUsers() {
    return this.http.get<any[]>(
      `${this.apiUrl}/users`
    );
  }
saveDescription(data: any) {

  return this.http.post(
    'http://127.0.0.1:8000/metadata/save-description',
    data
  );

}
getAIContext() {
  return this.http.get(
    'http://127.0.0.1:8000/ai-context'
  );
}
getActiveConnector() {

  return this.http.get(
    'http://127.0.0.1:8000/active-connector'
  );

}
extractMetadata(id: number) {

  return this.http.post(
    `http://127.0.0.1:8000/metadata/extract/${id}`,
    {}
  );

}

  addUser(user: any) {
    return this.http.post(
      `${this.apiUrl}/users`,
      user
    );
  }

  deleteUser(id: number) {
    return this.http.delete(
      `${this.apiUrl}/users/${id}`
    );
  }

  updateUser(id: number, user: any) {
    return this.http.put(
      `${this.apiUrl}/users/${id}`,
      user
    );
  }

}