import { CanActivateFn } from '@angular/router';
import { inject } from '@angular/core';
import { Router } from '@angular/router';

export const roleGuard = (roles: string[]): CanActivateFn => {

  return () => {

    const router = inject(Router);

    const role = localStorage.getItem('role');

    if (role && roles.includes(role)) {
      return true;
    }

    router.navigate(['/dashboard']);
    return false;
  };

};