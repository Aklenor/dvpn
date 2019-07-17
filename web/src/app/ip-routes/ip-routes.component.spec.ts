import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { IpRoutesComponent } from './ip-routes.component';

describe('IpRoutesComponent', () => {
  let component: IpRoutesComponent;
  let fixture: ComponentFixture<IpRoutesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ IpRoutesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(IpRoutesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
