import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';


import { AddRouteDialogComponent } from './modal_windows/add-route-dialog.component';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { MonitoringComponent } from './monitoring/monitoring.component';
import { IpRoutesComponent } from './ip-routes/ip-routes.component';
import { VpsManagementComponent } from './vps-management/vps-management.component';
import { ParticlesComponent } from './particles/particles.component';
import { EditVpsModal } from './modal_windows/edit-vps-modal.component';
import { RequestsService } from './requests.service';
import { sshKeyOverview } from './vps-management/vps-management.component';

import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatMenuModule } from '@angular/material/menu';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatBottomSheetModule } from '@angular/material/bottom-sheet';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSnackBarModule } from '@angular/material/snack-bar';


import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
@NgModule({
  declarations: [
    AppComponent,
    MonitoringComponent,
    IpRoutesComponent,
    VpsManagementComponent,
    ParticlesComponent,
    EditVpsModal,
    AddRouteDialogComponent,
    sshKeyOverview
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,
    BrowserAnimationsModule,
    MatMenuModule,
    MatDividerModule,
    MatIconModule,
    MatFormFieldModule,
    MatToolbarModule,
    MatInputModule,
    MatProgressBarModule,
    CommonModule,
    MatCardModule,
    MatTableModule,
    MatExpansionModule,
    MatBottomSheetModule,
    MatButtonModule,
    MatSnackBarModule,
    AppRoutingModule,
    MatProgressSpinnerModule,
    MatDialogModule
  ],
  providers: [RequestsService],
  entryComponents: [
    EditVpsModal,
    AddRouteDialogComponent,
    sshKeyOverview
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
