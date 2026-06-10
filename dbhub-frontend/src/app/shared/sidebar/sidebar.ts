import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [
    RouterModule,
    CommonModule
  ],
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css']
})
export class Sidebar implements OnInit {

  userRole = '';

  constructor(
    private router: Router
  ) {}

  ngOnInit(): void {

    this.userRole =
      localStorage.getItem('role') || '';

    console.log(
      'Logged In Role:',
      this.userRole
    );

  }

  logout() {

    localStorage.clear();

    this.router.navigate(['/login']);

  }

}