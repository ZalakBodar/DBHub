import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login.html',
 styleUrls:['./login.css']
})
export class Login {

  email = '';
  password = '';

  constructor(
    private http: HttpClient,
    private router: Router
  ) {}

  login() {

    this.http.post<any>(
      'http://127.0.0.1:8000/login',
      {
        email: this.email,
        password: this.password
      }
    ).subscribe({

      next: (response) => {

        if (!response.success) {
          alert(response.message);
          return;
        }

        localStorage.setItem(
          'user',
          JSON.stringify(response)
        );

        localStorage.setItem(
          'role',
          response.role
        );

        alert('Login Successful');

        this.router.navigate(['/dashboard']);
      },

      error: (err) => {
        console.error(err);
        alert('Invalid Email or Password');
      }

    });

  }
}