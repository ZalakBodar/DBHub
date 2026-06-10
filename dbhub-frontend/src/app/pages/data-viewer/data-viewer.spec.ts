import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DataViewer } from './data-viewer';

describe('DataViewer', () => {
  let component: DataViewer;
  let fixture: ComponentFixture<DataViewer>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DataViewer],
    }).compileComponents();

    fixture = TestBed.createComponent(DataViewer);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
