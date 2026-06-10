import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import * as XLSX from 'xlsx';

@Component({
  selector: 'app-ai-assistant',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    HttpClientModule
  ],
  templateUrl: './ai-assistant.html',
  styleUrls: ['./ai-assistant.css']
})
export class AiAssistant {

  question = '';

  generatedSql = '';

  rows: any[] = [];

  count = 0;

  executionTime = 0;

  loading = false;

  objectKeys = Object.keys;

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  askAI() {

    if (!this.question.trim()) {

      alert('Enter a question');

      return;

    }

    this.loading = true;

    this.generatedSql = '';

    this.rows = [];

    this.count = 0;

    this.executionTime = 0;

    this.http.post<any>(
      'http://127.0.0.1:8000/ask-ai',
      {
        question: this.question
      }
    )
    .subscribe({

      next: (res) => {

        console.log('API Response:', res);

        this.loading = false;

        if (res.error) {

          alert(res.error);

          return;

        }

        this.generatedSql = res.sql || '';

        this.rows = res.answer || [];

        this.count = res.count || 0;

        this.executionTime =
          res.executionTime || 0;

        this.cdr.detectChanges();

      },

      error: (err) => {

        this.loading = false;

        console.error(err);

        alert(
          err?.error?.error ||
          'AI Error'
        );

      }

    });

  }

  copySQL() {

    if (!this.generatedSql) {

      alert('No SQL Available');

      return;

    }

    navigator.clipboard.writeText(
      this.generatedSql
    );

    alert('SQL Copied');

  }

  exportToExcel() {

    if (!this.rows.length) {

      alert('No Data');

      return;

    }

    const worksheet =
      XLSX.utils.json_to_sheet(
        this.rows
      );

    const workbook =
      XLSX.utils.book_new();

    XLSX.utils.book_append_sheet(
      workbook,
      worksheet,
      'Result'
    );

    XLSX.writeFile(
      workbook,
      'AI_Result.xlsx'
    );

  }

}