import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MetadataService } from '../../services/metadata.service';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})
export class Dashboard implements OnInit {

  totalTables = 0;
  totalUsers = 0;

databaseStatus = '';
connectorType = '';
databaseName = '';
serverName = '';

  activities: string[] = [];

  constructor(
    private metadataService: MetadataService,
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {

    this.loadDashboard();

    this.loadDatabaseHealth();

    this.loadActiveConnector();

  }
  loadDashboard() {

    // Total Tables
    this.metadataService.getTables().subscribe({

      next: (data: any[]) => {

        this.totalTables = data.length;

        this.cdr.detectChanges();

      },

      error: (err) => {

        console.error('Tables Error:', err);

      }

    });

    // Total Users
    this.http.get<any[]>(
      'http://127.0.0.1:8000/users'
    ).subscribe({

      next: (data) => {

        this.totalUsers = data.length;

        this.cdr.detectChanges();

      },

      error: (err) => {

        console.error('Users Error:', err);

      }

    });

    // Recent Activities
    this.http.get<string[]>(
      'http://127.0.0.1:8000/activities'
    ).subscribe({

      next: (data) => {

        this.activities = data;

        this.cdr.detectChanges();

      },

      error: (err) => {

        console.error('Activities Error:', err);

      }

    });

  }

  loadDatabaseHealth() {

    this.http.get<any>(
      'http://127.0.0.1:8000/database-health'
    ).subscribe({

      next: (data) => {

        this.databaseStatus = data.status;

        this.databaseName = data.database;

        this.serverName = data.server;

        this.cdr.detectChanges();

      },

      error: (err) => {

        console.error('Database Health Error:', err);

      }

    });

  }
loadActiveConnector() {

  this.http.get<any>(
    'http://127.0.0.1:8000/active-connector'
  ).subscribe({

    next: (data) => {

      this.connectorType = data.db_type;

      this.databaseName = data.name;

      if (data.db_type === 'MSSQL') {

        this.serverName = 'SQL Server';

      }

      else if (data.db_type === 'POSTGRESQL') {

        this.serverName = 'PostgreSQL';

      }

      else if (data.db_type === 'ORACLE') {

        this.serverName = 'Oracle';

      }

      this.cdr.detectChanges();

    },

    error: (err) => {

      console.error(
        'Active Connector Error:',
        err
      );

    }

  });

}

}