# Base-R figure generation at manuscript width; no external packages required.
args <- commandArgs(trailingOnly=TRUE)
root <- if (length(args)) args[1] else '.'
d <- read.csv(file.path(root, 'revisionPlan/rerun2026/phase_summary.csv'))
colors <- c(CDR='#b54f24', CCC='#1b7089')
make_plot <- function(name, metrics, titles) {
  png(file.path(root, paste0('figures/',name,'.png')), width=1800, height=1440,
      res=330, pointsize=9, type='cairo')
  par(mfrow=c(2,3), mar=c(2.7,3.6,3.5,.6), oma=c(.3,.2,.4,0), mgp=c(2.1,.6,0),
      tcl=-.22, cex.axis=.83, cex.lab=.9, las=1)
  for (family in c('HRL','NF')) for (i in seq_along(metrics)) {
    z <- d[d$metric==metrics[i] & startsWith(d$condition,paste0(family,'-')),]
    bounds <- range(c(z$ci95_low,z$ci95_high))
    if (diff(bounds)==0) bounds<-bounds+c(-1,1)
    pad <- diff(bounds)*.08
    plot(NA, xlim=c(.8,3.2), ylim=bounds+c(-pad,pad), xlab='', ylab='',
         xaxt='n', main='')
    mtext(family,side=3,line=2.0,cex=.85,font=2)
    mtext(titles[i],side=3,line=.7,cex=.76,font=2)
    axis(1, at=1:3, labels=c('Pre','During','Post'))
    abline(h=axTicks(2), col='#e5e5e5',lwd=.5)
    for (order in c('CDR','CCC')) {
      a<-z[z$condition==paste0(family,'-',order),];a<-a[order(a$phase),]
      x<-a$phase+if(order=='CDR') -.035 else .035
      lines(x,a$mean,col=colors[order],lwd=1.2)
      keep <- a$ci95_high > a$ci95_low
      if (any(keep)) arrows(x[keep],a$ci95_low[keep],x[keep],a$ci95_high[keep],angle=90,code=3,length=.035,col=colors[order],lwd=.8)
      points(x,a$mean,col=colors[order],pch=if(order=='CDR')16 else 17,cex=.65)
    }
    if (i==1) legend('topleft',legend=c('CDR','CCC'),col=colors,pch=c(16,17),
                      lty=1,bty='n',cex=.72,inset=.01)
    box()
  }
  dev.off()
}
make_plot('rerun-primary-results',c('homeostatic-mae','setpoint-dev','reward-total'),
          c('Mean absolute h','Population SD of h','Total objective reward'))
make_plot('rerun-regulation-results',c('setpoint-avg','homeostatic-rms','homeostatic-fraction-within-5'),
          c('Signed mean h','RMS h','Fraction within +/-5'))
