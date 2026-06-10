import { Component } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';

import { Sidebar } from './shared/sidebar/sidebar';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    Sidebar,
    CommonModule
  ],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App {

  constructor(public router: Router) {}

}