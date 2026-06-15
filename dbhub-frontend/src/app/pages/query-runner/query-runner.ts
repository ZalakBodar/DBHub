import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { ChangeDetectorRef } from '@angular/core';

@Component({
  selector: 'app-query-runner',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './query-runner.html',
  styleUrls: ['./query-runner.css']
})
export class QueryRunner {

  query = '';

  results: any[] = [];

  objectKeys = Object.keys;

  constructor(
  private http: HttpClient,
  private cdr: ChangeDetectorRef
) {}

  runQuery() {

    if (!this.query.trim()) {

      alert('Enter SQL Query');

      return;

    }

    this.http.post<any[]>(
      'http://127.0.0.1:8000/execute-query',
      {
        query: this.query
      }
    )
    .subscribe({

      next: (data) => {

  console.log("QUERY RESULT");
  console.log(data);

  this.results = [...data];

  this.cdr.detectChanges();

},

error: (err) => {

  console.error(err);

  alert(
    err?.error?.message ||
    err?.message ||
    'Query Failed'
  );

}

  })}}