import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChangeDetectorRef } from '@angular/core';

import { MetadataService } from '../../services/metadata.service';

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './users.html',
  styleUrls: ['./users.css']
})
export class Users implements OnInit {

  users: any[] = [];

  loading = true;

  name = '';
  email = '';
  role = 'Viewer';

  editingId: number | null = null;

constructor(
  private metadataService: MetadataService,
  private cdr: ChangeDetectorRef
) {}

 ngOnInit(): void {

  console.log('Users Page Loaded');

  this.loadUsers();

}

loadUsers() {

  this.metadataService
    .getUsers()
    .subscribe({

      next: (data: any) => {

        console.log('Users Loaded:', data);

        this.users = [...data];

        this.cdr.detectChanges();

      },

      error: (err) => {

        console.error(err);

      }

    });

}

  saveUser() {

    const userData = {
      name: this.name,
      email: this.email,
      role: this.role
    };

    if (this.editingId !== null) {

      this.metadataService
        .updateUser(this.editingId, userData)
        .subscribe({

          next:  () => {

            alert('User Updated');

            this.resetForm();

            this.loadUsers();

          },

          error: (err) => {

            console.error(err);

          }

        });

    } else {

      this.metadataService
        .addUser(userData)
        .subscribe({

          next: () => {

            alert('User Added');

            this.resetForm();

            this.loadUsers();

          },

          error: (err) => {

            console.error(err);

          }

        });

    }

  }

  editUser(user: any) {

    this.editingId = user.Id;

    this.name = user.Name;
    this.email = user.Email;
    this.role = user.Role;

  }

  deleteUser(id: number) {

    if (!confirm('Delete this user?')) {
      return;
    }

    this.metadataService
      .deleteUser(id)
      .subscribe({

        next: () => {

          alert('User Deleted');

          this.loadUsers();

        },

        error: (err) => {

          console.error(err);

        }

      });

  }

  resetForm() {

    this.editingId = null;

    this.name = '';
    this.email = '';
    this.role = 'Viewer';

  }

}