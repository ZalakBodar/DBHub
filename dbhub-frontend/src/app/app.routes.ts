import { Routes } from '@angular/router';

import { Login } from './pages/login/login';
import { Dashboard } from './pages/dashboard/dashboard';
import { Connectors } from './pages/connectors/connectors';
import { Metadata } from './pages/metadata/metadata';
import { DataViewer } from './pages/data-viewer/data-viewer';
import { Users } from './pages/users/users';

import { authGuard } from './guards/auth.guard';
import { roleGuard } from './guards/role.guard';

import { AiAssistant } from './pages/ai-assistant/ai-assistant';
import { QueryRunner } from './pages/query-runner/query-runner';
import { QueryHistoryComponent } from './pages/query-history/query-history';
import { Relationships } from './pages/relationships/relationships';
export const routes: Routes = [

  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },

  {
    path: 'login',
    component: Login
  },

  {
    path: 'dashboard',
    component: Dashboard,
    canActivate: [authGuard]
  },

  {
    path: 'connectors',
    component: Connectors,
    canActivate: [
      authGuard,
      roleGuard(['Admin'])
    ]
  },
{
  path: 'relationships',
  component: Relationships
},
  {
    path: 'metadata',
    component: Metadata,
    canActivate: [
      authGuard,
      roleGuard(['Admin', 'Developer'])
    ]
  },
  {
  path: 'query-runner',
  component: QueryRunner
},

{
  path: 'ai-assistant',
  component: AiAssistant
},
  {
    path: 'data-viewer',
    component: DataViewer,
    canActivate: [authGuard]
  },
{
  path: 'query-history',
  component: QueryHistoryComponent
},

  {
    path: 'users',
    component: Users,
    canActivate: [
      authGuard,
      roleGuard(['Admin'])
    ]
  },

  {
    path: '**',
    redirectTo: 'login'
  }



];