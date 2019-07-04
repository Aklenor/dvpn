import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { MonitoringComponent } from './monitoring/monitoring.component';
import { IpRoutesComponent } from './ip-routes/ip-routes.component';
import { VpsManagementComponent } from './vps-management/vps-management.component';


const routes: Routes = [
{ path: '', redirectTo: '/routing', pathMatch: 'full' },
{ path: 'monitoring', component: MonitoringComponent },
{ path: 'routing', component: IpRoutesComponent },
{ path: 'management', component: VpsManagementComponent }];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
