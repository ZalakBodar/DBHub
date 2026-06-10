import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MetadataService } from '../../services/metadata.service';
import { ChangeDetectorRef } from '@angular/core';

@Component({
  selector: 'app-query-history',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './query-history.html',
  styleUrls: ['./query-history.css']
})
export class QueryHistoryComponent implements OnInit {

  history: any[] = [];

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

        console.log(data);

        this.history = [...data];

        this.cdr.detectChanges();

      },

      error: (err) => {
        console.error(err);
      }

    });
}}