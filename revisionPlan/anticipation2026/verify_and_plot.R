# Independent R verification of all new contrasts; base R only.
args <- commandArgs(trailingOnly=TRUE)
root <- if (length(args)) args[1] else 'revisionPlan/anticipation2026'
d <- read.csv(file.path(root,'trial_metrics.csv'), check.names=FALSE)
p <- read.csv(file.path(root,'primary_contrasts.csv'), check.names=FALSE)
s <- read.csv(file.path(root,'sensitivity.csv'), check.names=FALSE)
summary <- read.csv(file.path(root,'phase_summary.csv'), check.names=FALSE)
metrics <- unique(p$metric)
near <- function(a,b) stopifnot(isTRUE(all.equal(a,b,tolerance=2e-8,check.attributes=FALSE)))
values <- function(f,o,phase,m,ids=0:249) {
  x <- d[d$family==f & d$order==o & d$phase==phase,]
  x[match(ids,x$trial),m]
}
for (i in seq_len(nrow(summary))) {
  r <- summary[i,]; pieces <- strsplit(r$condition,'-',fixed=TRUE)[[1]]
  x <- values(pieces[1],tolower(pieces[2]),r$phase,r$metric)
  near(r$mean,mean(x)); near(r$sd,sd(x)); near(r$median,median(x))
  margin <- qt(.975,249)*sd(x)/sqrt(250)
  near(r$ci95_low,mean(x)-margin);near(r$ci95_high,mean(x)+margin)
}
verify <- function(table, sensitivity=FALSE) {
  rawp <- numeric(nrow(table))
  for (i in seq_len(nrow(table))) {
    r <- table[i,]; ids <- 0:249
    if (r$method=='paired-exact-scene') {
      # Reconstruct exact-scene membership from immutable JSON through Python;
      # these row IDs are exported by build_analysis.py for this independent check.
      ids <- read.csv(file.path(root,'exact_scene_pairs.csv'))
      ids <- ids$trial[ids$family==r$family]
    }
    x <- values(r$family,'cdr',r$phase,r$metric,ids)
    y <- values(r$family,'ccc',r$phase,r$metric,ids)
    if (r$method %in% c('Welch-change','paired-change')) {
      x <- x-values(r$family,'cdr',1,r$metric,ids)
      y <- y-values(r$family,'ccc',1,r$metric,ids)
    }
    paired <- startsWith(r$method,'paired')
    # R cannot t.test two constant samples; handle that mathematical case.
    se2 <- if (paired) var(x-y)/length(x) else var(x)/length(x)+var(y)/length(y)
    if (se2==0) {
      ci <- rep(mean(x)-mean(y),2); pp <- as.numeric(mean(x)==mean(y))
    } else {
      t <- t.test(x,y,paired=paired); ci <- t$conf.int;pp <- t$p.value
    }
    near(r$difference,mean(x)-mean(y));near(r$ci95_low,ci[1]);near(r$ci95_high,ci[2]);near(r$p,pp)
    rawp[i] <- pp
  }
  for (phase in c(2,3)) for (method in unique(table$method)) {
    indices <- which(table$phase==phase & table$method==method)
    near(table$p_holm[indices],p.adjust(rawp[indices],method='holm'))
  }
}
verify(p);verify(s,TRUE)
writeLines(sprintf('PASS: R independently reproduced %d descriptive rows, %d primary contrasts and %d sensitivity contrasts, including confidence intervals, p values and Holm corrections.',nrow(summary),nrow(p),nrow(s)),file.path(root,'r_verification.txt'))

colors <- c(CDR='#b54f24',CCC='#1b7089')
plot_panels <- function(name,kind='phases') {
  draw <- function() {
    par(mfrow=c(2,3),mar=c(3.2,3.8,3.2,.7),oma=c(.2,.2,.2,0),mgp=c(2.2,.65,0),tcl=-.22,las=1)
    for (family in c('HRL','NF')) for (m in c('homeostatic-mae','setpoint-dev','reward-total')) {
      title <- c('homeostatic-mae'='Mean absolute h','setpoint-dev'='Population SD of h','reward-total'='Objective reward per phase')[[m]]
      z <- summary[startsWith(summary$condition,paste0(family,'-')) & summary$metric==m,]
      if (kind=='post') z <- z[z$phase==3,]
      bounds <- range(c(0,z$ci95_low,z$ci95_high));pad <- diff(bounds)*.05
      plot(NA,xlim=if(kind=='post')c(.6,2.4) else c(.8,3.2),ylim=bounds+c(-pad,pad),xlab='',ylab='',xaxt='n',main='')
      mtext(paste(family,title,sep=': '),side=3,line=1,cex=.86,font=2)
      abline(h=axTicks(2),col='#e5e5e5',lwd=.5)
      if(kind=='post') axis(1,at=1:2,labels=c('CDR','CCC')) else axis(1,at=1:3,labels=c('Pre','During','Post'))
      for (o in c('CDR','CCC')) {
        a <- z[z$condition==paste0(family,'-',o),];a <- a[order(a$phase),]
        x <- if(kind=='post') match(o,c('CDR','CCC')) else a$phase+if(o=='CDR')-.035 else .035
        if(kind!='post') lines(x,a$mean,col=colors[o],lwd=1.3)
        keep <- a$ci95_high>a$ci95_low
        if(any(keep)) arrows(x[keep],a$ci95_low[keep],x[keep],a$ci95_high[keep],angle=90,code=3,length=.04,col=colors[o])
        points(x,a$mean,col=colors[o],pch=if(o=='CDR')16 else 17,cex=.8)
      }
      if(m=='homeostatic-mae' && kind!='post') legend('topleft',legend=c('CDR','CCC'),col=colors,pch=c(16,17),lty=1,bty='n',cex=.8)
      box()
    }
  }
  pdf(file.path(root,paste0(name,'.pdf')),width=10,height=6,pointsize=10);draw();dev.off()
  png(file.path(root,paste0(name,'.png')),width=2200,height=1320,res=220,type='cairo',pointsize=10);draw();dev.off()
}
plot_panels('phase_outcomes')
plot_panels('post_outcomes','post')
