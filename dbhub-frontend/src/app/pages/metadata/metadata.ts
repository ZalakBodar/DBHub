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
  activeConnectorId = 0;
  tables: string[] = [];

  selectedTable = '';

  columns: any[] = [];

  constructor(
  private metadataService: MetadataService,
  private cdr: ChangeDetectorRef
) {}
ngOnInit(): void {

  this.loadActiveConnector();

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
loadActiveConnector() {

  this.metadataService.getActiveConnector().subscribe({

    next: (res: any) => {

      console.log("FULL RESPONSE =", res);

      this.activeConnectorId = res.id;

      console.log("Active Connector =", this.activeConnectorId);

    },

    error: (err) => {

      console.error("Active Connector Error:", err);

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

}
saveDescription(column: any) {

  const payload = {

    connector_id: this.activeConnectorId,
    table_name: this.selectedTable,
    column_name: column.column_name,
    description: column.description

  };

  console.log("SAVE PAYLOAD =", payload);

  this.metadataService.saveDescription(payload).subscribe({

    next: (res: any) => {

      console.log("Saved Successfully", res);
      alert("Description Saved");

    },

    error: (err) => {

      console.error("Save Error", err);

    }

  });

}
extractMetadata() {

  this.metadataService
    .getActiveConnector()
    .subscribe((connector: any) => {

      this.metadataService
        .extractMetadata(connector.id)
        .subscribe((res: any) => {

          alert(res.message);

        });

    });

}}