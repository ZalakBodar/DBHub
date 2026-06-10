import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-connectors',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './connectors.html',
  styleUrls: ['./connectors.css']
})
export class Connectors implements OnInit {

  connectorName = '';
  databaseType = 'MSSQL';
  host = '';
  port = '';
  username = '';
  password = '';
  databaseName = '';

  connectors: any[] = [];

  onDatabaseTypeChange() {

if (this.databaseType === 'MSSQL' && !this.port) {
  this.port = '1433';
}

  if (this.databaseType === 'POSTGRESQL') {
    this.port = '5432';
  }

  if (this.databaseType === 'ORACLE') {
    this.port = '1521';
  }

}

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

ngOnInit(): void {

  this.onDatabaseTypeChange();

  this.loadConnectors();
}

  loadConnectors() {

    this.http.get<any[]>(
      'http://127.0.0.1:8000/connectors'
    )
    .subscribe({

      next: (data) => {

        this.connectors = [...data];

        this.cdr.detectChanges();

      },

      error: (err) => {

        console.error(err);

      }

    });
    

  }

  saveConnector() {

  if (
    !this.connectorName.trim() ||
    !this.host.trim() ||
    !this.port ||
    !this.databaseName.trim()
  ) {

    alert('Please fill all required fields');

    return;
  }

  const connector = {

    name: this.connectorName,
    db_type: this.databaseType,
    host: this.host,
    port: Number(this.port),
    username: this.username,
    password: this.password,
    database: this.databaseName

  };

  this.http.post(
    'http://127.0.0.1:8000/connectors',
    connector
  )
  .subscribe({

   next: (response: any) => {

  if (response.success) {

    alert(response.message);

    this.loadConnectors();

    this.connectorName = '';
    this.host = '';
    this.port = '';
    this.username = '';
    this.password = '';
    this.databaseName = '';

  } else {

    alert(response.message);

  }

}

  });

}
testConnection() {

  if (
    !this.host.trim() ||
    !this.databaseName.trim()
  ) {

    alert('Host and Database Name required');

    return;
  }

  const connector = {

    name: this.connectorName,
    db_type: this.databaseType,
    host: this.host,
    port: Number(this.port),
    username: this.username,
    password: this.password,
    database: this.databaseName

  };

  this.http.post<any>(
    'http://127.0.0.1:8000/test-connection',
    connector
  )
  .subscribe({

    next: (response) => {

      if (response.success) {

        alert('Connection Successful');

      } else {

        alert(response.message);

      }

    },

    error: () => {

      alert('Connection Failed');

    }

  });

}
deleteConnector(connectorId: number) {

  if (!confirm('Delete this connector?')) {
    return;
  }

  this.http.delete(
    `http://127.0.0.1:8000/connectors/${connectorId}`
  )
  .subscribe({

    next: () => {



      this.loadConnectors();

    },

    error: (err) => {

      console.error(err);

      alert('Delete failed');

    }

  });

}}