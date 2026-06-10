import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MetadataService } from '../../services/metadata.service';

@Component({
  selector: 'app-relationships',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './relationships.html',
  styleUrls: ['./relationships.css']
})
export class Relationships implements OnInit {

  relationships: any[] = [];

  loading = true;

  constructor(
    private metadataService: MetadataService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadRelationships();
  }

  loadRelationships() {

    this.loading = true;

    this.metadataService
      .getRelationships()
      .subscribe({

        next: (data) => {

          console.log('Relationships:', data);

          this.relationships = data;

          this.loading = false;

          this.cdr.detectChanges();
        },

        error: (err) => {

          console.error(err);

          this.loading = false;

          this.cdr.detectChanges();
        }

      });
  }
}