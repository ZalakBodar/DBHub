import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import * as XLSX from 'xlsx';

import { MetadataService } from '../../services/metadata.service';

@Component({
  selector: 'app-data-viewer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './data-viewer.html',
  styleUrls: ['./data-viewer.css']
})
export class DataViewer implements OnInit {

  tables: string[] = [];

  selectedTable = '';

  rows: any[] = [];

  filteredRows: any[] = [];

  pagedRows: any[] = [];

  searchText = '';

  objectKeys = Object.keys;

  currentPage = 1;

  pageSize = 10;

  constructor(
    private metadataService: MetadataService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {

    console.log('Data Viewer Loaded');

    this.loadTables();

  }

  loadTables() {

    this.metadataService.getTables().subscribe({

      next: (data: string[]) => {

        this.tables = [...data];

        this.cdr.detectChanges();

      },

      error: (err) => {

        console.error(err);

      }

    });

  }

  loadData() {

    if (!this.selectedTable) {

      alert('Please select a table');

      return;

    }

    this.metadataService
      .getTableData(this.selectedTable)
      .subscribe({

        next: (data: any[]) => {

          this.rows = [...data];

          this.filteredRows = [...data];

          this.currentPage = 1;

          this.updatePagination();

          console.log('Rows:', data);

          this.cdr.detectChanges();

        },

        error: (err) => {

          console.error(err);

        }

      });

  }

  filterData() {

    const search = this.searchText.toLowerCase();

    this.filteredRows = this.rows.filter(row =>

      Object.values(row).some(value =>

        String(value)
          .toLowerCase()
          .includes(search)

      )

    );

    this.currentPage = 1;

    this.updatePagination();

    this.cdr.detectChanges();

  }

  updatePagination() {

    const start =
      (this.currentPage - 1) * this.pageSize;

    const end =
      start + this.pageSize;

    this.pagedRows =
      this.filteredRows.slice(start, end);

  }

  nextPage() {

    const totalPages =
      Math.ceil(
        this.filteredRows.length /
        this.pageSize
      );

    if (this.currentPage < totalPages) {

      this.currentPage++;

      this.updatePagination();

    }

  }

  previousPage() {

    if (this.currentPage > 1) {

      this.currentPage--;

      this.updatePagination();

    }

  }

  exportToExcel() {

    if (!this.filteredRows.length) {

      alert('No data available');

      return;

    }

    const worksheet =
      XLSX.utils.json_to_sheet(
        this.filteredRows
      );

    const workbook =
      XLSX.utils.book_new();

    XLSX.utils.book_append_sheet(
      workbook,
      worksheet,
      'Data'
    );

    XLSX.writeFile(
      workbook,
      `${this.selectedTable}.xlsx`
    );

  }

}