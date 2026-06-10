import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChangeDetectorRef } from '@angular/core';

import { MetadataService } from '../../services/metadata.service';

@Component({
  selector: 'app-metadata',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './metadata.html',
  styleUrls: ['./metadata.css']
})
export class Metadata implements OnInit {

  tables: string[] = [];

  selectedTable = '';

  columns: any[] = [];

  constructor(
  private metadataService: MetadataService,
  private cdr: ChangeDetectorRef
) {}
ngOnInit(): void {

  this.loadTables();

}

loadTables() {

  this.metadataService.getTables().subscribe({

    next: (data: string[]) => {

      this.tables = data;

      this.selectedTable = '';

      this.columns = [];

      this.cdr.detectChanges();

    },

    error: (err) => {

      console.error(err);

    }

  });

}

  loadMetadata() {

  if (!this.selectedTable) return;

this.metadataService
  .getMetadata(this.selectedTable)
    .subscribe({

      next: (data) => {

        this.columns = [...data];

        this.cdr.detectChanges();

      },

      error: (err) => {

        console.error(err);

      }

    });

}}