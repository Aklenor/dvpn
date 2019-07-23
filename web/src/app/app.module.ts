import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { MonitoringComponent } from './monitoring/monitoring.component';
import { IpRoutesComponent } from './ip-routes/ip-routes.component';
import { VpsManagementComponent } from './vps-management/vps-management.component';
import { ParticlesComponent } from './particles/particles.component'; 
import {EditVpsModal} from './vps-management/edit-vps-modal.component';
import { HttpClientModule } from '@angular/common/http';
import { RequestsService } from './requests.service';


import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatMenuModule } from '@angular/material/menu';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import {MatButtonModule} from '@angular/material/button'; 
import {MatFormFieldModule} from '@angular/material/form-field'; 
import {MatInputModule} from '@angular/material';
import {MatExpansionModule} from '@angular/material/expansion'; 
import {MatCardModule} from '@angular/material/card'; 
import {MatTableModule} from '@angular/material/table'; 
import {MatProgressBarModule} from '@angular/material/progress-bar'; 
import {MatToolbarModule} from '@angular/material/toolbar'; 
import {MatBottomSheetModule} from '@angular/material/bottom-sheet'; 

@NgModule({
  declarations: [
    AppComponent,
    MonitoringComponent,
    IpRoutesComponent,
    VpsManagementComponent,
    ParticlesComponent,
    EditVpsModal
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
    AppRoutingModule
  ],
  providers: [RequestsService],
  entryComponents: [
    EditVpsModal
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
