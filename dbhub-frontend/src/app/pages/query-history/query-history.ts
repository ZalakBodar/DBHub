import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MetadataService } from '../../services/metadata.service';
import { ChangeDetectorRef } from '@angular/core';

@Component({
  selector: 'app-query-history',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './query-history.html',
  styleUrls: ['./query-history.css']
})
export class QueryHistoryComponent implements OnInit {

  history: any[] = [];
  filteredHistory: any[] = [];

  searchText = '';

  constructor(
    private metadataService: MetadataService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadHistory();
  }

  loadHistory() {

    this.metadataService
      .getQueryHistory()
      .subscribe({

        next: (data) => {

          this.history = data;

          this.filteredHistory = [...data];

          this.cdr.detectChanges();
        },

        error: (err) => {
          console.error(err);
        }

      });

  }
formatDate(date: string): string {

  return new Date(date).toLocaleString();

}
  filterHistory() {

    const search = this.searchText.toLowerCase();

    this.filteredHistory = this.history.filter(item =>
      item.Question?.toLowerCase().includes(search) ||
      item.SQLQuery?.toLowerCase().includes(search)
    );

  }

  copySQL(sql: string) {

    navigator.clipboard.writeText(sql);

    alert('SQL copied');

  }

}