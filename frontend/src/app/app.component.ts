import { Component, OnInit } from '@angular/core';
import { RouterOutlet, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterModule,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    MatButtonModule
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  title = 'IBM Banking Data Pipeline';

  menuItems = [
    { path: '/dashboard', icon: 'dashboard', label: 'Dashboard' },
    { path: '/upload', icon: 'cloud_upload', label: 'Upload Data' },
    { path: '/datasets', icon: 'storage', label: 'Datasets' },
    { path: '/anomalies', icon: 'warning', label: 'Anomalies' },
    { path: '/metrics', icon: 'analytics', label: 'Metrics' }
  ];

  ngOnInit(): void {
    console.log('IBM Banking Pipeline Frontend Initialized');
  }
}
